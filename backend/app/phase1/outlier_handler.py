from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats


# ─── per-column method selector ────────────────────────────────────────────────

def _select_outlier_method(series: pd.Series, n_rows: int) -> str:
    """
    AI rule-based selection of outlier treatment method per column.
    - small dataset (<200 rows)  → IQR (robust, no normality assumption)
    - approximately normal (|skew|<1 and |kurtosis|<3) → ZScore
    - extreme range (max/min ratio >100 and range > 1000) → Clipping
    - default → IQR
    """
    clean = series.dropna()
    if len(clean) < 4:
        return "iqr"

    if n_rows < 200:
        return "iqr"

    try:
        skewness = float(clean.skew())
        kurt = float(clean.kurtosis())
    except Exception:
        return "iqr"

    range_val = float(clean.max()) - float(clean.min())
    min_abs = abs(float(clean.min()))
    # Very wide range (many orders of magnitude) → clipping
    if min_abs > 0 and (float(clean.max()) / min_abs) > 100 and range_val > 1000:
        return "clipping"

    # Near-normal → ZScore
    if abs(skewness) < 1.0 and abs(kurt) < 3.0:
        return "zscore"

    return "iqr"


# ─── outlier treatment implementations ─────────────────────────────────────────

def _apply_iqr(series: pd.Series) -> Tuple[pd.Series, int]:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return series, 0
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    return series.clip(lower=lower, upper=upper), int(mask.sum())


def _apply_zscore(series: pd.Series, threshold: float = 3.0) -> Tuple[pd.Series, int]:
    mean = series.mean()
    std = series.std()
    if std == 0:
        return series, 0
    z = (series - mean) / std
    mask = z.abs() > threshold
    lower = mean - threshold * std
    upper = mean + threshold * std
    return series.clip(lower=lower, upper=upper), int(mask.sum())


def _apply_clipping(series: pd.Series, lower_pct: float = 0.01, upper_pct: float = 0.99) -> Tuple[pd.Series, int]:
    lower = series.quantile(lower_pct)
    upper = series.quantile(upper_pct)
    mask = (series < lower) | (series > upper)
    return series.clip(lower=lower, upper=upper), int(mask.sum())


# ─── public API ────────────────────────────────────────────────────────────────

def cap_outliers_iqr(
    dataframe: pd.DataFrame,
    numeric_columns: List[str],
    target_column: str,
) -> tuple[pd.DataFrame, int]:
    """
    Backward-compatible entry point – now dispatches to per-column smart method.
    Returns (cleaned_df, total_outliers_capped).
    """
    df, report = handle_outliers(dataframe, numeric_columns=numeric_columns, target_column=target_column)
    total = sum(info["outliers_found"] for info in report.values())
    return df, total


def handle_outliers(
    dataframe: pd.DataFrame,
    numeric_columns: List[str],
    target_column: str,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    AI-driven per-column outlier handling.
    Returns (cleaned_df, per_column_report).
    """
    df = dataframe.copy()
    report: dict[str, Any] = {}
    n_rows = len(df)

    for column in numeric_columns:
        if column == target_column:
            continue
        if column not in df.columns:
            continue

        series = df[column].copy()
        method = _select_outlier_method(series, n_rows)

        if method == "zscore":
            df[column], n_outliers = _apply_zscore(series)
        elif method == "clipping":
            df[column], n_outliers = _apply_clipping(series)
        else:
            df[column], n_outliers = _apply_iqr(series)

        report[column] = {"method": method, "outliers_found": n_outliers}

    return df, report
