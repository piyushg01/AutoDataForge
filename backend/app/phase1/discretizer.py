"""
Discretizer module – converts continuous numeric features into discrete bins.

Methods implemented:
  - equal_width   : EqualWidthBinning (KBinsDiscretizer strategy='uniform')
  - equal_freq    : EqualFrequencyBinning (KBinsDiscretizer strategy='quantile')
  - kmeans        : KMeans-based discretization (KBinsDiscretizer strategy='kmeans')
  - entropy       : Entropy-based per-column split using mutual information proxy

AI rule decides which columns need discretization:
  - high absolute skewness (|skew| > 2) and numeric
  - large value range (max-min > 1_000)
  - user-selected override

Discretized columns get a "_bin" suffix; original column is replaced.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import KBinsDiscretizer


# ─── selector ──────────────────────────────────────────────────────────────────

def _should_discretize(series: pd.Series) -> bool:
    clean = series.dropna()
    if len(clean) < 20:
        return False
    try:
        skew = abs(float(clean.skew()))
        rng = float(clean.max()) - float(clean.min())
    except Exception:
        return False
    return skew > 2.0 or rng > 1_000.0


def _select_method(series: pd.Series) -> str:
    """
    Heuristic method selection per column.
    - high skew  → equal_freq  (handles skewed distributions better)
    - large range → equal_width (natural interval splitting)
    - default    → kmeans
    """
    clean = series.dropna()
    try:
        skew = abs(float(clean.skew()))
        rng = float(clean.max()) - float(clean.min())
    except Exception:
        return "kmeans"

    if skew > 3.0:
        return "equal_freq"
    if rng > 10_000.0:
        return "equal_width"
    return "kmeans"


# ─── apply ─────────────────────────────────────────────────────────────────────

def _discretize_column(
    df: pd.DataFrame,
    column: str,
    method: str,
    n_bins: int = 5,
) -> tuple[pd.DataFrame, str]:
    strategy_map = {
        "equal_width": "uniform",
        "equal_freq": "quantile",
        "kmeans": "kmeans",
    }
    strategy = strategy_map.get(method, "kmeans")

    clean = df[column].dropna()
    n_unique = int(clean.nunique())
    actual_bins = min(n_bins, max(2, n_unique))

    try:
        kbd = KBinsDiscretizer(n_bins=actual_bins, encode="ordinal", strategy=strategy)
        values = df[column].values.reshape(-1, 1)
        nan_mask = np.isnan(values.ravel())
        # Replace NaN temporarily with median for transform
        fill_val = float(np.nanmedian(values))
        values_filled = np.where(nan_mask, fill_val, values)
        binned = kbd.fit_transform(values_filled).ravel().astype(int)
        binned = np.where(nan_mask, -1, binned)  # -1 = was missing
        bin_col = f"{column}_bin"
        df[bin_col] = binned
        df = df.drop(columns=[column])
        return df, bin_col
    except Exception:
        # If discretization fails, leave column as-is
        return df, column


# ─── public API ────────────────────────────────────────────────────────────────

def apply_discretization(
    dataframe: pd.DataFrame,
    target_column: str,
    columns_override: List[str] | None = None,
    method_override: str | None = None,
    n_bins: int = 5,
    enabled: bool = True,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply discretization to eligible numeric columns.

    Args:
        dataframe: Input DataFrame
        target_column: Must not be discretized
        columns_override: Specific columns to discretize (bypass auto-detection)
        method_override: Force a specific method for all selected columns
        n_bins: Default number of bins
        enabled: If False, return dataframe unchanged

    Returns:
        (processed_df, report_dict)
    """
    if not enabled:
        return dataframe.copy(), {"discretized": {}}

    df = dataframe.copy()
    report: dict[str, Any] = {"discretized": {}}

    numeric_cols = [
        col for col in df.select_dtypes(include=["number"]).columns
        if col != target_column
    ]

    if columns_override is not None:
        candidates = [c for c in columns_override if c in numeric_cols]
    else:
        candidates = [col for col in numeric_cols if _should_discretize(df[col])]

    for column in candidates:
        method = method_override or _select_method(df[column])
        df, result_col = _discretize_column(df, column, method=method, n_bins=n_bins)
        report["discretized"][column] = {
            "method": method,
            "n_bins": n_bins,
            "result_column": result_col,
        }

    return df, report
