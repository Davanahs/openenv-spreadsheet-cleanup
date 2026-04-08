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
                # Add the whole group count
                total += int(len(group))
    return total

def build_issues_summary(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "missing": count_total_missing(df),
        "duplicates": detect_duplicates(df),
        "inconsistent": count_inconsistent_cells(df),
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

def get_detailed_issues(df: pd.DataFrame) -> List[Any]:
    """Return a list of detailed Issue objects for the frontend."""
    issues = []
    if df is None: return issues

    # 1. Missing values
    for col in df.columns:
        null_indices = df[df[col].isnull()].index.tolist()
        if null_indices:
            issues.append({
                "column": col,
                "type": "missing",
                "rows": null_indices
            })
            
    # 2. Duplicate rows
    cols_for_dup = [c for c in df.columns if c.lower() != "id"]
    if not cols_for_dup:
        cols_for_dup = list(df.columns)
    dup_mask = df.duplicated(subset=cols_for_dup, keep=False)
    dup_indices = df[dup_mask].index.tolist()
    if dup_indices:
        issues.append({
            "column": "Dataset",
            "type": "duplicate_rows",
            "rows": dup_indices
        })
        
    # 3. Inconsistent values
    for col in df.select_dtypes(include=["object", "string"]).columns:
        if col.lower() in ["id", "name", "email"]:
            continue
        valid_df = df[col].dropna().astype(str).str.strip()
        if valid_df.empty: continue
        lowered = valid_df.str.lower()
        counts = valid_df.groupby(lowered).nunique()
        inconsistent_lowered = counts[counts > 1].index.tolist()
        
        if inconsistent_lowered:
            rows = df[df[col].astype(str).str.lower().isin(inconsistent_lowered)].index.tolist()
            issues.append({
                "column": col,
                "type": "inconsistent",
                "rows": rows
            })
            
    return issues