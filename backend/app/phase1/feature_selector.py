"""
Feature Selection module – three strategies:

Filter methods (fast, model-agnostic):
  - Low variance removal
  - High correlation removal (threshold 0.95)
  - Mutual Information scoring (classification/regression)

Wrapper methods (search-based, expensive – skipped for large datasets):
  - Skipped in favor of embedded for this phase

Embedded methods (feature importance from tree models):
  - ExtraTreesClassifier / ExtraTreesRegressor feature importances
  - Keep top-N features by importance

AI auto-selects the combination based on dataset size and problem type.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor
from sklearn.feature_selection import SelectKBest, mutual_info_classif, mutual_info_regression


# ─── helper utilities ───────────────────────────────────────────────────────────

def _is_id_like(column_name: str) -> bool:
    lowered = column_name.lower()
    return lowered == "id" or lowered.endswith("_id") or lowered.endswith("id")


def _remove_low_variance(df: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, List[str]]:
    """Drop columns with only one unique value (zero variance)."""
    dropped = []
    for col in list(df.columns):
        if col == target_column:
            continue
        if df[col].nunique(dropna=False) <= 1:
            df = df.drop(columns=[col])
            dropped.append(col)
    return df, dropped


def _remove_high_correlation(
    df: pd.DataFrame,
    target_column: str,
    threshold: float = 0.95,
) -> tuple[pd.DataFrame, List[str]]:
    """Remove one of each pair of numeric features with correlation > threshold."""
    numeric_cols = [
        col for col in df.select_dtypes(include=["number"]).columns
        if col != target_column
    ]
    if len(numeric_cols) < 2:
        return df, []

    corr_matrix = df[numeric_cols].corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = [col for col in upper.columns if any(upper[col] > threshold)]
    df = df.drop(columns=to_drop, errors="ignore")
    return df, to_drop


def _mutual_info_selection(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    k_ratio: float = 0.8,
) -> tuple[pd.DataFrame, List[str], Dict[str, float]]:
    """Keep top k_ratio fraction of numeric features by mutual information score."""
    numeric_cols = [
        col for col in df.select_dtypes(include=["number"]).columns
        if col != target_column
    ]
    if len(numeric_cols) < 3:
        return df, [], {}

    X = df[numeric_cols].values
    X = np.nan_to_num(X, nan=0.0)

    y = df[target_column].values
    if problem_type == "classification":
        try:
            y_int = pd.factorize(y)[0]
            scores = mutual_info_classif(X, y_int, discrete_features=False, random_state=42)
        except Exception:
            return df, [], {}
    else:
        try:
            y_float = pd.to_numeric(pd.Series(y), errors="coerce").fillna(0).values
            scores = mutual_info_regression(X, y_float, random_state=42)
        except Exception:
            return df, [], {}

    score_map = {col: float(scores[i]) for i, col in enumerate(numeric_cols)}

    # Keep features with score above threshold (keep at least 2)
    sorted_cols = sorted(score_map, key=lambda c: score_map[c], reverse=True)
    n_keep = max(2, int(len(sorted_cols) * k_ratio))
    keep = set(sorted_cols[:n_keep])
    drop = [col for col in numeric_cols if col not in keep]

    if drop:
        df = df.drop(columns=drop, errors="ignore")

    return df, drop, score_map


def _embedded_selection(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    top_n_ratio: float = 0.85,
) -> tuple[pd.DataFrame, List[str], Dict[str, float]]:
    """ExtraTrees feature importance – keep top top_n_ratio features."""
    numeric_cols = [
        col for col in df.select_dtypes(include=["number"]).columns
        if col != target_column
    ]
    if len(numeric_cols) < 3:
        return df, [], {}

    X = df[numeric_cols].values
    X = np.nan_to_num(X, nan=0.0)
    y = df[target_column].values

    try:
        if problem_type == "classification":
            y_int = pd.factorize(y)[0]
            model = ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X, y_int)
        else:
            y_float = pd.to_numeric(pd.Series(y), errors="coerce").fillna(0).values
            model = ExtraTreesRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            model.fit(X, y_float)
    except Exception:
        return df, [], {}

    importances = model.feature_importances_
    importance_map = {col: float(importances[i]) for i, col in enumerate(numeric_cols)}

    sorted_cols = sorted(importance_map, key=lambda c: importance_map[c], reverse=True)
    n_keep = max(2, int(len(sorted_cols) * top_n_ratio))
    keep = set(sorted_cols[:n_keep])
    drop = [col for col in numeric_cols if col not in keep]

    if drop:
        df = df.drop(columns=drop, errors="ignore")

    return df, drop, importance_map


# ─── public API ────────────────────────────────────────────────────────────────

def remove_unnecessary_columns(
    dataframe: pd.DataFrame,
    target_column: str,
    suggested_drop_columns: List[str],
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Drop explicitly suggested / identifier / constant / high-cardinality text columns.
    (Backward-compatible – called early in the pipeline before encoding.)
    """
    df = dataframe.copy()
    dropped: list[str] = []

    for column in list(df.columns):
        if column == target_column:
            continue

        if column in suggested_drop_columns:
            df = df.drop(columns=[column])
            dropped.append(column)
            continue

        if _is_id_like(column):
            df = df.drop(columns=[column])
            dropped.append(column)
            continue

        if df[column].nunique(dropna=False) <= 1:
            df = df.drop(columns=[column])
            dropped.append(column)
            continue

        unique_ratio = float(df[column].nunique(dropna=True) / max(len(df), 1))
        if unique_ratio >= 0.95 and not pd.api.types.is_numeric_dtype(df[column]):
            df = df.drop(columns=[column])
            dropped.append(column)

    selected_features = [column for column in df.columns if column != target_column]
    return df, {
        "dropped_columns": sorted(set(dropped)),
        "selected_features": selected_features,
    }


def run_feature_selection(
    dataframe: pd.DataFrame,
    target_column: str,
    problem_type: str = "classification",
    use_mutual_info: bool = True,
    use_embedded: bool = True,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Full multi-method feature selection pipeline.
    Run AFTER encoding + scaling.

    Steps:
      1. Remove zero-variance columns
      2. Remove highly correlated pairs (filter)
      3. Mutual information based selection (filter)
      4. ExtraTrees importance (embedded)

    Returns:
        (processed_df, report_dict)
    """
    df = dataframe.copy()
    report: dict[str, Any] = {
        "low_variance_dropped": [],
        "high_correlation_dropped": [],
        "mutual_info_dropped": [],
        "embedded_dropped": [],
        "mutual_info_scores": {},
        "feature_importances": {},
        "selected_features": [],
    }

    # 1. Low variance
    df, lv_drop = _remove_low_variance(df, target_column)
    report["low_variance_dropped"] = lv_drop

    # 2. High correlation filter
    df, hc_drop = _remove_high_correlation(df, target_column)
    report["high_correlation_dropped"] = hc_drop

    # 3. Mutual information (filter)
    if use_mutual_info:
        df, mi_drop, mi_scores = _mutual_info_selection(df, target_column, problem_type)
        report["mutual_info_dropped"] = mi_drop
        report["mutual_info_scores"] = mi_scores

    # 4. Embedded (feature importance)
    if use_embedded:
        df, emb_drop, fi_scores = _embedded_selection(df, target_column, problem_type)
        report["embedded_dropped"] = emb_drop
        report["feature_importances"] = fi_scores

    report["selected_features"] = [col for col in df.columns if col != target_column]
    return df, report


def add_optional_derived_features(dataframe: pd.DataFrame, datetime_columns: List[str]) -> pd.DataFrame:
    """Legacy helper kept for backward compatibility."""
    df = dataframe.copy()
    for column in datetime_columns:
        parsed = pd.to_datetime(df[column], errors="coerce")
        if parsed.notna().any():
            df[f"{column}_year"] = parsed.dt.year
            df[f"{column}_month"] = parsed.dt.month
            df[f"{column}_day"] = parsed.dt.day
            df = df.drop(columns=[column])
    return df
