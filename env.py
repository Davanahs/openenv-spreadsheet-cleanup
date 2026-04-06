import pandas as pd
from utils import (
    detect_missing,
    detect_duplicates,
    detect_inconsistent,
    normalize_column,
    fill_missing
)
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ---------------- AI AGENT ----------------
class SimpleAgent:
    def __init__(self):
        self.action_scores = {}

    def select_action(self, observation):
        print("\n---- AGENT THINKING ----")
        issues = observation["issues"]
        actions = []

        for col in issues["inconsistent_columns"]:
            actions.append(("normalize_values", col))

        if issues["duplicate_count"] > 0:
            actions.append(("remove_duplicates", None))

        for col in issues["missing_columns"]:
            actions.append(("fill_missing", col))

        if not actions:
            print("No actions available")
            return None

        best = max(actions, key=lambda a: self.action_scores.get(a, 0))
        print("Decision:", best)

        return {"action_type": best[0], "column": best[1]}

    def update(self, action, reward):
        print("Agent learning. Reward:", reward)
        key = (action["action_type"], action.get("column"))
        self.action_scores[key] = self.action_scores.get(key, 0) + reward


# ---------------- ENV ----------------
class SpreadsheetCleanupEnv:

    def __init__(self):
        print("Environment initialized")
        self.df = None
        self.step_count = 0
        self.max_steps = 10
        self.agent = SimpleAgent()

    def reset(self, data):
        print("Reset called")
        if isinstance(data, dict) and "data" in data:
            data = data["data"]

        self.df = pd.DataFrame(data)
        self.step_count = 0

        return self._get_observation()

    def step(self, action=None):
        print("\n================ STEP", self.step_count + 1, "================")

        if self.df is None:
            return {"error": "Load data first"}

        # -------- BEFORE STATE --------
        before_df = self.df.copy()
        observation = self._get_observation()

        print("\n---- AGENT OBSERVATION (BEFORE) ----")
        print(observation)

        print("\n---- DATA BEFORE ----")
        print(before_df.head())

        self.step_count += 1
        reward = 0.0

        # -------- AGENT DECISION --------
        if action is None:
            action = self.agent.select_action(observation)
            if action is None:
                print("\nNo actions available")
                return {
                    "observation": observation,
                    "reward": 1.0,
                    "done": True,
                    "available_actions": []
                }

        print("\n---- AGENT ACTION ----")
        print(action)

        action_type = action.get("action_type")
        column = action.get("column")

        # -------- APPLY ACTION --------
        try:
            if action_type == "fill_missing":
                self.df = fill_missing(self.df, column)
                reward = 0.3

            elif action_type == "normalize_values":
                self.df = normalize_column(self.df, column)
                reward = 0.25

            elif action_type == "remove_duplicates":
                before = len(self.df)
                self.df = self.df.drop_duplicates()
                reward = 0.3 if len(self.df) < before else 0

        except Exception as e:
            print("Step error:", e)
            reward = -0.2

        # -------- AFTER STATE --------
        print("\n---- DATA AFTER ----")
        print(self.df.head())

        print("\n---- REWARD ----")
        print(reward)

        self.agent.update(action, reward)

        print("====================================\n")

        return {
            "observation": self._get_observation(),
            "reward": reward,
            "done": self.step_count >= self.max_steps,
            "available_actions": self._available_actions()
        }

    def auto_clean(self):
        print("Auto clean started")
        history = []

        for _ in range(self.max_steps):
            action = self.agent.select_action(self._get_observation())
            if action is None:
                break

            result = self.step(action)
            history.append(result)

        print("Auto clean finished")

        return {
            "message": "AI auto clean complete",
            "history": history,
            "final": self.state()
        }

    def _get_observation(self):
        if self.df is None:
            return {}

        return {
            "columns": list(self.df.columns),
            "issues": {
                "missing_columns": list(detect_missing(self.df)),
                "duplicate_count": int(detect_duplicates(self.df)),
                "inconsistent_columns": list(detect_inconsistent(self.df))
            },
            "step_count": int(self.step_count)
        }

    def _available_actions(self):
        actions = []
        obs = self._get_observation()

        for col in obs["issues"]["missing_columns"]:
            actions.append({"action_type": "fill_missing", "column": col})

        for col in obs["issues"]["inconsistent_columns"]:
            actions.append({"action_type": "normalize_values", "column": col})

        if obs["issues"]["duplicate_count"] > 0:
            actions.append({"action_type": "remove_duplicates", "column": None})

        return actions

    def state(self):
        if self.df is None:
            return {"error": "No data loaded"}

        clean_df = self.df.copy()
        clean_df = clean_df.replace({pd.NA: None})
        clean_df = clean_df.where(pd.notnull(clean_df), None)

        return {
            "data": clean_df.to_dict(),
            "step_count": int(self.step_count)
        }