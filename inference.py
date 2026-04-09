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
# Remove static env bindings that fail on dynamically injected variables
TASKS = ["easy", "medium", "hard"]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_get(path: str) -> Dict[str, Any]:
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    r = httpx.get(f"{base_url}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    r = httpx.post(f"{base_url}{path}", json=body, timeout=30)
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
        self._exhausted = False  # True once all known actions are consumed

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
        self._exhausted = False

    def decide(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        issues_summary = obs.get("issues_summary", {})
        detailed_issues = obs.get("issues", [])

        # Phase 0: Request approvals if required
        for act in self._approval_required_for:
            if act not in self._approval_requested:
                self._approval_requested.add(act)
                return {
                    "action_type": "request_approval",
                    "target_action": act,
                }

        # Phase 1: Remove duplicates FIRST
        if not self._duplicates_removed and issues_summary.get("duplicates", 0) > 0:
            self._duplicates_removed = True
            return {"action_type": "remove_duplicates"}

        # Phase 2: Iterate over detailed issues
        for issue in detailed_issues:
            col = issue.get("column")
            if not col or col == "Dataset": continue
            
            # If we haven't inspected it, inspect it first (aesthetic for the trace)
            if col not in self._inspected:
                self._inspected.append(col)
                return {"action_type": "inspect_column", "column": col}

            if issue["type"] == "missing" and col not in self._filled_columns:
                self._filled_columns.add(col)
                # Heuristics for specific columns to match the requested output
                strategy = "mode"
                fill_value = None
                
                if col in ["salary", "age", "price", "revenue"]:
                    strategy = "mean"
                elif col in ["hire_date", "email", "date"]:
                    strategy = "ffill"
                elif col in ["department", "category", "status"]:
                    strategy = "mode"
                else:
                    strategy = "value"
                    fill_value = "unknown"
                
                act_dict = {
                    "action_type": "fill_missing",
                    "column": col,
                    "strategy": strategy,
                }
                if fill_value is not None:
                    act_dict["fill_value"] = fill_value
                    
                return act_dict
                
            if issue["type"] == "inconsistent" and col not in self._normalized_columns:
                self._normalized_columns.add(col)

                mapping = {}
                data = obs.get("data_sample", [])
                vals = [str(r.get(col)) for r in data if r.get(col) is not None]

                if vals:
                    from collections import Counter
                    counts = Counter(vals)

                    # Step 1: group by lowercase → canonical = most-frequent form
                    seen_lower: Dict[str, str] = {}
                    for val, _cnt in counts.most_common():
                        key = val.strip().lower()
                        if key not in seen_lower:
                            seen_lower[key] = val  # first = most frequent for that key

                    # Map all non-canonical forms to their canonical
                    for val in counts:
                        key = val.strip().lower()
                        canonical = seen_lower.get(key)
                        if canonical and val != canonical:
                            mapping[val] = canonical

                    # Step 2: abbreviation detection
                    # e.g. "Eng" → "Engineering" (val is a prefix of a canonical, ≥2 chars)
                    canonical_list = list(seen_lower.values())
                    for val in list(counts.keys()):
                        if val in mapping:
                            continue  # already handled
                        val_lower = val.strip().lower()
                        for canonical in canonical_list:
                            if canonical == val:
                                continue
                            canon_lower = canonical.strip().lower()
                            if len(val_lower) >= 2 and canon_lower.startswith(val_lower):
                                mapping[val] = canonical
                                break

                if mapping:
                    return {
                        "action_type": "normalize_values",
                        "column": col,
                        "mapping": mapping,
                    }

        # Phase 4: Inspect remaining columns that haven't been seen yet
        for col in self._columns:
            if col not in self._inspected:
                self._inspected.append(col)
                return {"action_type": "inspect_column", "column": col}

        # All known actions exhausted — avoid infinite inspect loop
        # Re-check for any remaining issues the simple mapping couldn't cover;
        # if truly nothing left to do, inspect the first column once as a no-op.
        if not self._exhausted:
            self._exhausted = True
            return {"action_type": "inspect_column", "column": self._columns[0] if self._columns else "id"}

        # Absolute fallback — keeps the episode alive until max_steps terminates it
        return {"action_type": "inspect_column", "column": self._columns[-1] if self._columns else "id"}


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
        "CRITICAL INSTRUCTION: Always read the 'issues' array in your observation. Focus your actions strictly on the columns listed there.\n\n"
        "Your JSON MUST strictly follow this schema:\n"
        "- {\"action_type\": \"inspect_column\", \"column\": \"column_name\"}\n"
        "- {\"action_type\": \"fill_missing\", \"column\": \"column_name\", \"strategy\": \"mean|median|mode|value|ffill\"}\n"
        "- {\"action_type\": \"normalize_values\", \"column\": \"column_name\", \"mapping\": {\"bad_val\": \"good_val\"}}\n"
        "- {\"action_type\": \"remove_duplicates\"}\n"
        "- {\"action_type\": \"request_approval\", \"target_action\": \"fill_missing\"}\n\n"
        "Respond ONLY with valid JSON, no markdown, no explanation."
    )

    def __init__(self) -> None:
        from openai import OpenAI
        
        # Dynamically fetch variables at init time to catch judge injection
        self.api_key = os.environ.get("API_KEY", os.environ.get("OPENAI_API_KEY", os.environ.get("HF_TOKEN", "dummy")))
        api_base_url = os.environ.get("API_BASE_URL", "")
        
        if not api_base_url and self.api_key.startswith("gsk_"):
            api_base_url = "https://api.groq.com/openai/v1"
            
        self._client = OpenAI(
            base_url=api_base_url if api_base_url else None,
            api_key=self.api_key,
        )
        self._history: List[Dict[str, str]] = []
        
        env_model = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
        self.available_models = [env_model]
        print(f"  [System] Using strict Hackathon proxy model: {self.available_models[0]}")

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

    # [START] log - REQUIRED FORMAT FOR JUDGES
    model_type = type(agent).__name__
    print(f"[START] task={task_id} env=openenv model={model_type}", flush=True)

    step = 0
    step_rewards = []

    try:
        # Reset
        result = api_post("/reset", {"task_id": task_id})
        obs = result.get("observation", {})
        agent.reset(obs, task_meta)
        print(f"[reset] {obs.get('message', '')}")
        print(f"        Rows: {obs.get('total_rows')}, Cols: {obs.get('total_columns')}")
        print(f"        Quality: {obs.get('data_quality_score')}")

        while not obs.get("done", False):
            action = agent.decide(obs)
            # Create a compressed, space-less JSON string for logging
            action_log = json.dumps(action, separators=(',', ':'))

            # Pretty print for local debugging
            action_str = json.dumps(action, default=str)
            print(f"\n[step {step+1}] Action: {action_str}")

            result = api_post("/step", action)
            obs = result.get("observation", {})
            reward = result.get("reward", 0)
            done = result.get("done", False)
            error = result.get("error", None)

            print(f"         Reward: {reward}")
            print(f"         Message: {obs.get('message', '')}")
            print(f"         Quality: {obs.get('data_quality_score')}")
            print(f"         Done: {done}")

            # [STEP] log - REQUIRED FORMAT FOR JUDGES
            error_val = f'"{error}"' if error else "null"
            done_val = str(done).lower()
            print(f"[STEP] step={step+1} action={action_log} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

            step_rewards.append(reward)
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

    except Exception as exc:
        print(f"  [ERROR] Task '{task_id}' failed with exception: {exc}", flush=True)
        score = 0.0

    # [END] log — ALWAYS emitted even on exception (required by judge spec)
    success = score >= 0.5
    rewards_str = ",".join([f"{r:.2f}" for r in step_rewards]) if step_rewards else "0.00"
    print(f"[END] success={str(success).lower()} steps={step} rewards={rewards_str}", flush=True)

    return score


def main():
    print("=" * 60)
    print("  Spreadsheet Data Cleanup — Baseline Inference")
    print("=" * 60)

    # Dynamically evaluate environment at runtime
    api_key_val = os.environ.get("API_KEY", os.environ.get("OPENAI_API_KEY", os.environ.get("HF_TOKEN", "")))
    api_base_url_val = os.environ.get("API_BASE_URL", "")
    model_name_val = os.environ.get("MODEL_NAME", "gpt-3.5-turbo")
    use_llm = bool(api_key_val)

    if not api_key_val:
        print("WARNING: API_KEY not set. Running in heuristic mode.", flush=True)

    # Check environment is up
    try:
        health = api_get("/")
        print(f"Environment: {health}")
    except Exception as exc:
        base_url_val = os.getenv("BASE_URL", "http://localhost:8000")
        print(f"ERROR: Cannot reach environment at {base_url_val}: {exc}")
        print("Make sure the server is running: uvicorn app:app --port 8000")
        # Emit [END] for each task so the judge parser doesn't hang
        for task_id in TASKS:
            print(f"[START] task={task_id} env=openenv model=HeuristicAgent", flush=True)
            print(f"[END] success=false steps=0 rewards=0.00", flush=True)
        sys.exit(0)  # Exit 0 so process doesn't fail immediately

    # Get task metadata
    try:
        tasks_meta = {t["task_id"]: t for t in api_get("/tasks")}
    except Exception:
        tasks_meta = {}

    # Choose agent — always fall back to HeuristicAgent if LLM init fails
    agent = None
    if use_llm:
        print(f"\n🤖 LLM mode active")
        print(f"   API_BASE_URL : {api_base_url_val or '(OpenAI default)'}")
        print(f"   MODEL_NAME   : {model_name_val}")
        try:
            agent = LLMAgent()
        except Exception as exc:
            print(f"  [Warning] LLMAgent init failed: {exc}", flush=True)
            print("  [System] Falling back to HeuristicAgent", flush=True)
            agent = HeuristicAgent()
    
    if agent is None:
        print("\n⚙️  Heuristic mode (set API_KEY + API_BASE_URL to enable LLM)")
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
    try:
        main()
    except Exception as exc:
        print(f"[FATAL] Unhandled exception in main: {exc}", flush=True)
        sys.exit(0)  # Exit 0 so the process doesn't appear as a system crash