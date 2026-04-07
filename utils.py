import pandas as pd
from typing import Dict, Any, List

def count_total_missing(df: pd.DataFrame) -> int:
    return int(df.isnull().sum().sum())

def count_total_issues(df: pd.DataFrame) -> int:
    return count_total_missing(df) + detect_duplicates(df) + count_inconsistent_cells(df)

def detect_duplicates(df: pd.DataFrame) -> int:
    cols = [c for c in df.columns if c.lower() != "id"]
    if not cols:
        cols = list(df.columns)
    return int(df.duplicated(subset=cols).sum())

def detect_missing(df: pd.DataFrame) -> List[str]:
    return [col for col in df.columns if df[col].isnull().any()]

def detect_inconsistent(df: pd.DataFrame) -> List[str]:
    inconsistent = []
    for col in df.select_dtypes(include=["object", "string"]).columns:
        if col.lower() == "id" or col.lower() == "email" or col.lower() == "name":
            continue
        valid_df = df[col].dropna().astype(str).str.strip()
        lowered = valid_df.str.lower()
        if lowered.nunique() != valid_df.nunique():
            inconsistent.append(col)
    return inconsistent

def count_inconsistent_cells(df: pd.DataFrame) -> int:
    total = 0
    inconsistent_cols = detect_inconsistent(df)
    for col in inconsistent_cols:
        valid_df = df[col].dropna().astype(str).str.strip()
        lowered = valid_df.str.lower()
        # Find which lowered strings have more than 1 variant
        grouped = valid_df.groupby(lowered)
        for name, group in grouped:
            if group.nunique() > 1:
                # Add the number of items that are not the most frequent variant?
                # Or just add the whole group? The environment says "normalized X values"
                # Let's just track total inconsistent cells as the count of all such groups
                total += int(len(group))
    return total

def build_issues_summary(df: pd.DataFrame) -> Dict[str, Any]:
    missing_dict = df.isnull().sum().to_dict()
    missing_values = {k: int(v) for k, v in missing_dict.items() if v > 0}
    
    inconsistent_columns = {}
    cols = detect_inconsistent(df)
    for col in cols:
        valid_df = df[col].dropna().astype(str).str.strip()
        lowered = valid_df.str.lower()
        grouped = valid_df.groupby(lowered)
        groups_dict = {}
        for name, group in grouped:
            unique_vals = list(group.unique())
            if len(unique_vals) > 1:
                # Use the lowercase as canonical, or the most frequent one
                canonical = pd.Series(unique_vals).str.title().mode()[0] if name else unique_vals[0]
                groups_dict[canonical] = unique_vals
        if groups_dict:
            inconsistent_columns[col] = groups_dict

    return {
        "missing_values": missing_values,
        "duplicate_rows": detect_duplicates(df),
        "inconsistent_columns": inconsistent_columns
    }

def compute_data_quality_score(df: pd.DataFrame, initial_missing: int, initial_duplicates: int, initial_inconsistent: int) -> float:
    current_missing = count_total_missing(df)
    current_duplicates = detect_duplicates(df)
    current_inconsistent = count_inconsistent_cells(df)
    
    initial_total = initial_missing + initial_duplicates + initial_inconsistent
    if initial_total == 0:
        return 1.0
        
    current_total = current_missing + current_duplicates + current_inconsistent
    score = max(0.0, 1.0 - (current_total / initial_total))
    return float(score)

def deterministic_approval(action_type_str: str, approved_actions: set) -> bool:
    return action_type_str in approved_actions