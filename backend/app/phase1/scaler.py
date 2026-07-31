from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, Normalizer, RobustScaler, StandardScaler


# ─── per-column scaler selector ────────────────────────────────────────────────

def _select_scaler(series: pd.Series, has_outliers: bool) -> str:
    """
    AI rule-based scaler selection per numeric column.
    - outliers detected        → RobustScaler
    - near-normal (|skew|<1)   → StandardScaler
    - all non-negative + small range  → MinMaxScaler
    - otherwise                → StandardScaler
    """
    clean = series.dropna()
    if len(clean) < 2:
        return "standard"

    if has_outliers:
        return "robust"

    try:
        skewness = float(clean.skew())
    except Exception:
        skewness = 0.0

    if abs(skewness) < 1.0:
        return "standard"

    if float(clean.min()) >= 0:
        return "minmax"

    return "standard"


_SCALER_MAP = {
    "standard": StandardScaler,
    "minmax": MinMaxScaler,
    "robust": RobustScaler,
    "normalizer": Normalizer,
}


# ─── public API ────────────────────────────────────────────────────────────────

def scale_features(
    dataframe: pd.DataFrame,
    target_column: str,
    outliers_detected: bool,
) -> tuple[pd.DataFrame, str]:
    """
    Backward-compatible single-scaler entry point.
    Picks one scaler for ALL numeric columns via majority-vote of per-column hints
    then delegates to scale_features_per_column.
    """
    df = dataframe.copy()
    numeric_columns = [
        col for col in df.select_dtypes(include=["number"]).columns
        if col != target_column
    ]
    if not numeric_columns:
        return df, "none"

    # Majority vote
    votes: dict[str, int] = {}
    for col in numeric_columns:
        hint = _select_scaler(df[col], has_outliers=outliers_detected)
        votes[hint] = votes.get(hint, 0) + 1

    chosen = max(votes, key=lambda k: votes[k])
    scaler_cls = _SCALER_MAP.get(chosen, StandardScaler)
    scaler = scaler_cls()
    df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
    return df, scaler_cls.__name__


def scale_features_per_column(
    dataframe: pd.DataFrame,
    target_column: str,
    outlier_report: Dict[str, Any] | None = None,
) -> tuple[pd.DataFrame, Dict[str, str]]:
    """
    Per-column scaler selection – returns (df, {column: scaler_name}).
    outlier_report: dict from handle_outliers() → column: {outliers_found: int, ...}
    """
    df = dataframe.copy()
    outlier_report = outlier_report or {}
    scaler_decisions: dict[str, str] = {}

    numeric_columns = [
        col for col in df.select_dtypes(include=["number"]).columns
        if col != target_column
    ]
    if not numeric_columns:
        return df, {}

    for column in numeric_columns:
        col_has_outliers = (outlier_report.get(column, {}).get("outliers_found", 0) > 0)
        hint = _select_scaler(df[column], has_outliers=col_has_outliers)
        scaler_cls = _SCALER_MAP.get(hint, StandardScaler)
        scaler = scaler_cls()
        df[[column]] = scaler.fit_transform(df[[column]])
        scaler_decisions[column] = scaler_cls.__name__

    return df, scaler_decisions
