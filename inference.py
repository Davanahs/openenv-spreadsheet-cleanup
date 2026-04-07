#!/usr/bin/env python3
"""
Baseline inference script for the Spreadsheet Data Cleanup OpenEnv environment.

Supports two modes:
    1. **Heuristic** (default) — deterministic rule-based agent; no LLM required.
    2. **LLM**      — uses an OpenAI-compatible chat model to decide actions.

Usage:
    # Heuristic mode (no env vars needed)
    python inference.py

    # LLM mode
    API_BASE_URL=http://localhost:11434/v1  MODEL_NAME=llama3  python inference.py

Environment variables:
    BASE_URL         - URL of the running environment server (default: http://localhost:8000)
    API_BASE_URL     - OpenAI-compatible API base URL (enables LLM mode)
    MODEL_NAME       - Model name for the LLM (default: gpt-3.5-turbo)
    HF_TOKEN         - Hugging Face token (optional, for HF-hosted models)
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
load_dotenv()
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL", "")         # empty → heuristic mode
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
TASKS = ["easy", "medium", "hard"]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_get(path: str) -> Dict[str, Any]:
    r = httpx.get(f"{BASE_URL}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    r = httpx.post(f"{BASE_URL}{path}", json=body, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Grader (inline — mirrors grader.py logic so script is self-contained)
# ---------------------------------------------------------------------------

def compute_score(state: Dict[str, Any]) -> float:
    initial = state.get("initial_issues", 1) or 1
    remaining = state.get("issues_remaining", 0)
    quality = state.get("data_quality_score", 0)
    steps = state.get("step_count", 0)
    max_steps = state.get("max_steps", 1) or 1
    unapproved = state.get("unapproved_attempts", 0)

    issues_fixed = max(0, min(1, (initial - remaining) / initial))
    efficiency = max(0, min(1, 1 - steps / max_steps))
    compliance = max(0, 1 - 0.25 * unapproved)

    return round(0.50 * issues_fixed + 0.30 * quality + 0.10 * efficiency + 0.10 * compliance, 4)


# ---------------------------------------------------------------------------
# Heuristic Agent
# ---------------------------------------------------------------------------

class HeuristicAgent:
    """
    Simple rule-based agent that:
    1. Inspects each column
    2. Requests approval if needed
    3. Removes duplicates
    4. Normalizes inconsistent values  
    5. Fills missing values
    """

    def __init__(self) -> None:
        self._inspected: List[str] = []
        self._approval_requested: set = set()
        self._duplicates_removed = False
        self._normalized_columns: set = set()
        self._filled_columns: set = set()
        self._columns: List[str] = []
        self._approval_required_for: List[str] = []

    def reset(self, obs: Dict[str, Any], task_meta: Optional[Dict] = None):
        self._inspected = []
        self._approval_requested = set()
        self._duplicates_removed = False
        self._normalized_columns = set()
        self._filled_columns = set()
        self._columns = obs.get("column_names", [])
        self._approval_required_for = (
            task_meta.get("approval_required_for", []) if task_meta else []
        )

    def decide(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        issues = obs.get("issues_summary", {})

        # Phase 0: Request approvals if required
        for act in self._approval_required_for:
            if act not in self._approval_requested:
                self._approval_requested.add(act)
                return {
                    "action_type": "request_approval",
                    "target_action": act,
                }

        # Phase 1: Remove duplicates FIRST (before other operations)
        if not self._duplicates_removed and issues.get("duplicate_rows", 0) > 0:
            self._duplicates_removed = True
            return {"action_type": "remove_duplicates"}

        # Phase 2: Normalize inconsistent columns
        inconsistent = issues.get("inconsistent_columns", {})
        for col, groups in inconsistent.items():
            if col not in self._normalized_columns:
                self._normalized_columns.add(col)
                mapping = {}
                for canonical, variants in groups.items():
                    for v in variants:
                        mapping[v] = canonical
                if mapping:
                    return {
                        "action_type": "normalize_values",
                        "column": col,
                        "mapping": mapping,
                    }

        # Phase 3: Fill missing values (MOST IMPORTANT)
        missing = issues.get("missing_values", {})
        for col, count in missing.items():
            if col not in self._filled_columns and count > 0:
                self._filled_columns.add(col)
                return {
                    "action_type": "fill_missing",
                    "column": col,
                    "strategy": "mode",
                }

        # Phase 4: Inspect remaining columns (optional, low priority)
        for col in self._columns:
            if col not in self._inspected:
                self._inspected.append(col)
                return {"action_type": "inspect_column", "column": col}

        # All done — no more issues to fix
        return {"action_type": "inspect_column", "column": self._columns[0] if self._columns else "id"}


# ---------------------------------------------------------------------------
# LLM Agent
# ---------------------------------------------------------------------------

class LLMAgent:
    """Agent that uses an OpenAI-compatible chat model with dynamic multi-model fallback."""

    SYSTEM_PROMPT = (
        "You are a data cleaning AI agent. You interact with a spreadsheet cleanup "
        "environment. At each step you receive an observation and must return a JSON "
        "action. Available action types: inspect_column, fill_missing, "
        "normalize_values, remove_duplicates, request_approval.\n\n"
        "Your JSON MUST strictly follow this schema:\n"
        "- {\"action_type\": \"inspect_column\", \"column\": \"column_name\"}\n"
        "- {\"action_type\": \"fill_missing\", \"column\": \"column_name\", \"strategy\": \"mean|median|mode|value|ffill\"}\n"
        "- {\"action_type\": \"normalize_values\", \"column\": \"column_name\", \"mapping\": {\"bad_val\": \"good_val\"}}\n"
        "- {\"action_type\": \"remove_duplicates\"}\n"
        "- {\"action_type\": \"request_approval\", \"target_action\": \"fill_missing\"}\n\n"
        "Respond ONLY with valid JSON, no markdown, no explanation."
    )

    def __init__(self) -> None:
        from openai import OpenAI, AuthenticationError
        self.api_key = os.getenv("OPENAI_API_KEY", "dummy")
        
        # Automatically setup the correct base URL based on key prefix if possible
        api_base_url = API_BASE_URL
        if self.api_key.startswith("gsk_"):
            # It's a Groq key
            if "openai" in api_base_url.lower() and "groq" not in api_base_url.lower():
                api_base_url = "https://api.groq.com/openai/v1"
            elif not api_base_url:
                api_base_url = "https://api.groq.com/openai/v1"
        elif self.api_key.startswith("sk-") and not api_base_url:
            api_base_url = "https://api.openai.com/v1"
        
        self._client = OpenAI(
            base_url=api_base_url if api_base_url else None,
            api_key=self.api_key,
        )
        self._history: List[Dict[str, str]] = []
        
        # Dynamically fetch all models available for this API key
        print("  [System] Fetching available models for API key...")
        try:
            models_response = self._client.models.list()
            all_models = [m.id for m in models_response.data]
            
            # Filter out known non-text-generation models
            filtered_models = [m for m in all_models if all(
                block not in m.lower() for block in ["prompt-guard", "embed", "whisper", "tts", "dall-e", "vision", "moderation"]
            )]
            
            # 1. Start with the user's preferred MODEL_NAME if it's in the list
            self.available_models = []
            env_model = os.getenv("MODEL_NAME")
            if env_model and env_model in filtered_models:
                self.available_models.append(env_model)
                filtered_models.remove(env_model)
            
            # 2. Add all other valid chat models as fallbacks
            self.available_models.extend(filtered_models)
            
            if not self.available_models:
                # If everything was filtered or list is empty, use raw list as absolute last resort
                self.available_models = all_models[:3]

            print(f"  [System] Found {len(self.available_models)} available chat models.")
            print(f"  [System] Primary model: {self.available_models[0]}")

        except AuthenticationError as e:
            print(f"  [Error] Authentication failed: {e}")
            raise 
        except Exception as e:
            print(f"  [Error] Failed to fetch models: {e}")
            # Absolute fallback if API is down or list fails
            self.available_models = [os.getenv("MODEL_NAME") or "gpt-4o-mini"]

    def reset(self, obs: Dict[str, Any], task_meta=None):
        pass # History is built fresh each step to avoid context window limits

    def decide(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        from openai import AuthenticationError
        
        # Only pass the system prompt and the current observation. 
        # Appending history infinitely causes "Please reduce the length of messages" errors.
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Current Observation:\n{json.dumps(obs, indent=2, default=str)}"}
        ]
        
        action = None
        last_error = None
        
        # Iterate over all available models until one succeeds
        for model_name in self.available_models:
            try:
                resp = self._client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0,
                    max_tokens=300,
                )
                content = resp.choices[0].message.content.strip()
                
                try:
                    action = json.loads(content)
                except json.JSONDecodeError:
                    import re
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        action = json.loads(match.group())
                    else:
                        action = {"action_type": "inspect_column", "column": "id"}
                        
                # Move this successful model to the front of the list
                if self.available_models[0] != model_name:
                    self.available_models.remove(model_name)
                    self.available_models.insert(0, model_name)
                    
                return action
            except AuthenticationError as e:
                # If authentication fails, no fallback will work
                raise RuntimeError(f"Authentication Failed: {str(e)}")
            except Exception as e:
                last_error = e
                print(f"\n  [Warning] Model {model_name} failed: {type(e).__name__} - {str(e)}")
                print("  [System] Attempting fallback to the next available model...")
                continue # Try the next model

        raise RuntimeError(
            f"All {len(self.available_models)} available models failed. "
            f"Last error encountered: {str(last_error)}"
        )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run_task(task_id: str, agent, task_meta: Optional[Dict] = None):
    """Run a single task and return the final score."""
    print(f"\n{'='*60}")
    print(f"  TASK: {task_id}")
    print(f"{'='*60}")

    # Reset
    obs = api_post("/reset", {"task_id": task_id})
    agent.reset(obs, task_meta)
    print(f"[reset] {obs.get('message', '')}")
    print(f"        Rows: {obs.get('total_rows')}, Cols: {obs.get('total_columns')}")
    print(f"        Quality: {obs.get('data_quality_score')}")

    step = 0
    while not obs.get("done", False):
        action = agent.decide(obs)
        print(f"\n[step {step+1}] Action: {json.dumps(action, default=str)}")

        result = api_post("/step", action)
        obs = result.get("observation", {})
        reward = result.get("reward", 0)
        done = result.get("done", False)

        print(f"         Reward: {reward}")
        print(f"         Message: {obs.get('message', '')}")
        print(f"         Quality: {obs.get('data_quality_score')}")
        print(f"         Done: {done}")

        step += 1
        if done:
            break

    # Get final state & score
    final_state = api_get("/state")
    score = compute_score(final_state)

    print(f"\n--- FINAL RESULTS for '{task_id}' ---")
    print(f"  Steps used   : {final_state.get('step_count')} / {final_state.get('max_steps')}")
    print(f"  Issues fixed : {final_state.get('initial_issues', 0) - final_state.get('issues_remaining', 0)}"
          f" / {final_state.get('initial_issues', 0)}")
    print(f"  Quality score: {final_state.get('data_quality_score')}")
    print(f"  Unapproved   : {final_state.get('unapproved_attempts')}")
    print(f"  FINAL SCORE  : {score}")

    return score


def main():
    print("=" * 60)
    print("  Spreadsheet Data Cleanup — Baseline Inference")
    print("=" * 60)

    # Check environment is up
    try:
        health = api_get("/")
        print(f"Environment: {health}")
    except Exception as exc:
        print(f"ERROR: Cannot reach environment at {BASE_URL}: {exc}")
        print("Make sure the server is running: uvicorn app:app --port 8000")
        sys.exit(1)

    # Get task metadata
    tasks_meta = {t["task_id"]: t for t in api_get("/tasks")}

    # Choose agent
    if API_BASE_URL:
        print(f"\nInitializing LLM agent...")
        agent = LLMAgent()
    else:
        print("\nUsing heuristic agent (no LLM)")
        agent = HeuristicAgent()

    scores = {}
    for task_id in TASKS:
        meta = tasks_meta.get(task_id)
        scores[task_id] = run_task(task_id, agent, meta)

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for tid, s in scores.items():
        print(f"  {tid:10s} → {s}")
    avg = sum(scores.values()) / len(scores) if scores else 0
    print(f"  {'AVERAGE':10s} → {round(avg, 4)}")
    print()


if __name__ == "__main__":
    main()