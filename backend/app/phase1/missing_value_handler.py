from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer, SimpleImputer


def _knn_impute_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Apply KNN imputation to numeric columns."""
    if not columns:
        return df
    numeric_ref = df.select_dtypes(include=["number"]).columns.tolist()
    knn = KNNImputer(n_neighbors=5)
    df[numeric_ref] = knn.fit_transform(df[numeric_ref])
    return df


def handle_missing_values(dataframe: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    AI-driven missing value handling:
    - <5% missing  → mean (symmetric) or median (skewed numeric); mode for categorical
    - 5–30% missing → KNNImputer for numeric; mode for categorical
    - >30–40% missing → median/mode with warning
    - >40% missing  → suggest drop (never drop target)
    """
    df = dataframe.copy()
    actions: dict[str, str] = {}
    suggested_drop: list[str] = []
    knn_candidates: list[str] = []

    for column in df.columns:
        missing_pct = float(df[column].isna().mean() * 100)
        if missing_pct == 0:
            continue

        # >40% → suggest drop (protect target column)
        if missing_pct > 40 and column != target_column:
            suggested_drop.append(column)
            actions[column] = f"suggest_drop({missing_pct:.2f}%_missing)"
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            if missing_pct < 5:
                skew = float(df[column].skew(skipna=True)) if df[column].notna().any() else 0.0
                if abs(skew) < 1:
                    df[column] = df[column].fillna(df[column].mean())
                    actions[column] = "mean_impute"
                else:
                    df[column] = df[column].fillna(df[column].median())
                    actions[column] = "median_impute"
            elif missing_pct <= 30:
                # KNN imputation – defer actual transform after collecting all candidates
                knn_candidates.append(column)
                actions[column] = "knn_impute"
            else:
                # 30–40% → median fill (safe fallback)
                df[column] = df[column].fillna(df[column].median())
                actions[column] = "median_impute(heavy_missing)"
        else:
            # Categorical / text
            mode_vals = df[column].mode(dropna=True)
            fill_val = mode_vals.iloc[0] if not mode_vals.empty else "unknown"
            df[column] = df[column].fillna(fill_val)
            if missing_pct < 5:
                actions[column] = "mode_impute"
            elif missing_pct <= 30:
                actions[column] = "mode_impute(moderate_missing)"
            else:
                actions[column] = "mode_impute(heavy_missing)"

    # Apply KNN imputation in bulk on numeric block
    if knn_candidates:
        try:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            knn = KNNImputer(n_neighbors=min(5, max(1, len(df) // 10)))
            df[numeric_cols] = knn.fit_transform(df[numeric_cols])
        except Exception:
            # Fallback: median if KNN fails
            for col in knn_candidates:
                if df[col].isna().any():
                    df[col] = df[col].fillna(df[col].median())
                    actions[col] = "median_impute(knn_fallback)"

    return df, {"missing_actions": actions, "suggested_drop_columns": suggested_drop}
