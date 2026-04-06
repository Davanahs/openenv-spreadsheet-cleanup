import pandas as pd

def detect_missing(df):
    return [col for col in df.columns if df[col].isnull().any()]

def detect_duplicates(df):
    return int(df.duplicated().sum())

def detect_inconsistent(df):
    inconsistent = []
    for col in df.select_dtypes(include="object").columns:
        lowered = df[col].dropna().astype(str).str.lower()
        if lowered.nunique() != df[col].dropna().nunique():
            inconsistent.append(col)
    return inconsistent

def normalize_column(df, column):
    df[column] = df[column].astype(str).str.strip().str.upper()
    return df

def fill_missing(df, column):
    if column not in df.columns:
        return df

    # try numeric first
    try:
        if pd.api.types.is_numeric_dtype(df[column]):
            median = df[column].median()
            df[column] = df[column].fillna(median)
        else:
            df[column] = df[column].astype(str)
            df[column] = df[column].replace("nan", None)
            df[column] = df[column].fillna("UNKNOWN")

    except Exception as e:
        print("fill_missing error:", e)
        df[column] = df[column].fillna("UNKNOWN")

    return df