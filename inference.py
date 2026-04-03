import json
import os
from typing import Any, Dict, List

from openai import OpenAI

from tasks import list_tasks


API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY", "")


def log_start(task: str, env_name: str, model: str) -> None:
    print(f"[START] task={task} env={env_name} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: str | None = None) -> None:
    print(
        f"[STEP] step={step} action={action} reward={reward:.4f} done={done} error={error}",
        flush=True,
    )


def log_end(task: str, score: float, success: bool) -> None:
    print(f"[END] task={task} score={score:.4f} success={success}", flush=True)


def build_prompt(observation: Dict[str, Any]) -> str:
    return f"""
You are acting inside a spreadsheet cleanup environment.

Observation:
{json.dumps(observation, indent=2)}

Choose exactly one next action in JSON with keys:
- action_type
- column
- strategy

Allowed action_type values:
- inspect_column
- request_approval
- fill_missing
- normalize_values
- remove_duplicates

If a field is not needed, set it to null.
Return only JSON.
""".strip()


def heuristic_action(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback deterministic policy in case LLM output fails.
    This also helps keep baseline reproducible.
    """
    issues = observation.get("issues", {})
    missing_columns = issues.get("missing_columns", [])
    duplicate_count = issues.get("duplicate_count", 0)
    inconsistent_columns = issues.get("inconsistent_columns", [])
    approval_pending = observation.get("approval_pending", False)
    last_requested_approval = observation.get("last_requested_approval", {})

    if inconsistent_columns:
        return {
            "action_type": "normalize_values",
            "column": inconsistent_columns[0],
            "strategy": None,
        }

    if duplicate_count > 0:
        return {
            "action_type": "remove_duplicates",
            "column": None,
            "strategy": None,
        }

    if missing_columns:
        column = missing_columns[0]
        if not approval_pending and observation.get("approval_required_for", {}).get(column, False):
            return {
                "action_type": "request_approval",
                "column": column,
                "strategy": "default_fill",
            }

        if approval_pending:
            return {
                "action_type": "fill_missing",
                "column": last_requested_approval.get("column", column),
                "strategy": "default_fill",
            }

        return {
            "action_type": "fill_missing",
            "column": column,
            "strategy": "default_fill",
        }

    return {
        "action_type": "inspect_column",
        "column": observation.get("columns", [None])[0],
        "strategy": None,
    }


def get_model_action(client: OpenAI, observation: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_prompt(observation)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a careful spreadsheet cleaning agent."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        text = response.choices[0].message.content.strip()
        return json.loads(text)
    except Exception:
        return heuristic_action(observation)


def run_task(env, task_name: str, client: OpenAI) -> float:
    log_start(task=task_name, env_name="spreadsheet-cleanup-agent", model=MODEL_NAME)

    observation, info = env.reset(task_name=task_name)
    done = False
    final_score = 0.0
    step_num = 0

    while not done:
        step_num += 1
        try:
            action = get_model_action(client, observation)
            observation, reward, done, info = env.step(action)

            reward_value = reward["value"] if isinstance(reward, dict) else float(reward)
            final_score = float(info.get("score", final_score))

            log_step(
                step=step_num,
                action=json.dumps(action, separators=(",", ":")),
                reward=float(reward_value),
                done=bool(done),
                error=None,
            )
        except Exception as exc:
            log_step(step=step_num, action="{}", reward=0.0, done=True, error=str(exc))
            done = True

    success = final_score >= 0.8
    log_end(task=task_name, score=final_score, success=success)
    return final_score


def main() -> None:
    if not API_KEY:
        raise RuntimeError("Missing HF_TOKEN or OPENAI_API_KEY")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # This class must be implemented by your teammate in env.py
    from env import SpreadsheetCleanupEnv

    env = SpreadsheetCleanupEnv()

    scores: List[float] = []
    for task_name in list_tasks():
        score = run_task(env, task_name, client)
        scores.append(score)

    average_score = sum(scores) / len(scores) if scores else 0.0
    print(f"[END] task=all score={average_score:.4f} success={average_score >= 0.8}", flush=True)


if __name__ == "__main__":
    main()