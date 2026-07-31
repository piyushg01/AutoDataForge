from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def suggest_features(df: pd.DataFrame, target_column: str) -> List[Dict[str, Any]]:
    suggestions: List[Dict[str, Any]] = []

    numeric = [c for c in df.select_dtypes(include=["number"]).columns.tolist() if c != target_column]
    datelike = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "timestamp"]) ]

    if len(numeric) >= 2:
        a, b = numeric[0], numeric[1]
        suggestions.append({"type": "ratio", "feature": f"{a}_over_{b}", "columns": [a, b]})
        suggestions.append({"type": "difference", "feature": f"{a}_minus_{b}", "columns": [a, b]})

    if len(numeric) >= 3:
        a, b = numeric[0], numeric[2]
        suggestions.append({"type": "interaction", "feature": f"{a}_x_{b}", "columns": [a, b]})

    for col in datelike[:2]:
        suggestions.append({"type": "date_part", "feature": f"{col}_month", "columns": [col]})

    return suggestions


def create_feature(df: pd.DataFrame, suggestion: Dict[str, Any]) -> pd.DataFrame:
    out = df.copy()
    feature_type = suggestion.get("type")
    feature_name = suggestion.get("feature")
    columns = suggestion.get("columns", [])

    if feature_type == "ratio" and len(columns) == 2:
        a, b = columns
        out[feature_name] = out[a] / out[b].replace(0, 1)
    elif feature_type == "difference" and len(columns) == 2:
        a, b = columns
        out[feature_name] = out[a] - out[b]
    elif feature_type == "interaction" and len(columns) == 2:
        a, b = columns
        out[feature_name] = out[a] * out[b]
    elif feature_type == "date_part" and len(columns) == 1:
        a = columns[0]
        converted = pd.to_datetime(out[a], errors="coerce")
        out[feature_name] = converted.dt.month.fillna(0).astype(int)

    return out
