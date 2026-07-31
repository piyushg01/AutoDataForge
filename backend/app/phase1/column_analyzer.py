"""
AI-driven column analysis module.

For each column it decides:
  - keep / drop
  - encoding type (label, ordinal, onehot, binary_hash, none)
  - scaling type (StandardScaler, MinMaxScaler, RobustScaler, none)
  - outlier method (iqr, zscore, clipping, none)
  - feature selection eligibility (yes / no)
  - reason (human-readable)

Rules implemented:
  - ID pattern (unique ratio ≈ 1)         → drop (identifier)
  - Constant column (1 unique value)       → drop (constant)
  - >50% missing                           → drop (too_many_missing)
  - Binary (2 unique values)              → label encoding
  - Ordinal name/value pattern            → ordinal encoding
  - High cardinality text (unique>50 & ratio>0.15) → binary_hash encoding
  - Very high cardinality (ratio≥0.95)   → drop (high_cardinality)
  - Nominal categorical (≤20 unique)     → onehot encoding
  - Numeric near-normal                   → StandardScaler, zscore outlier
  - Numeric skewed                        → RobustScaler, iqr outlier
  - Numeric non-negative small range     → MinMaxScaler, iqr outlier
  - DateTime column                       → extract features
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


_ORDINAL_TOKENS = [
    "rank", "level", "grade", "stage", "tier", "class",
    "priority", "severity", "order", "degree",
]

_ORDINAL_VALUE_SETS: list[frozenset] = [
    frozenset({"low", "medium", "high"}),
    frozenset({"low", "medium", "high", "very high"}),
    frozenset({"small", "medium", "large"}),
    frozenset({"bad", "average", "good", "excellent"}),
    frozenset({"never", "rarely", "sometimes", "often", "always"}),
    frozenset({"none", "mild", "moderate", "severe"}),
]


def _is_id_like(column_name: str) -> bool:
    lowered = column_name.lower()
    return lowered == "id" or lowered.endswith("_id") or lowered.endswith("id")


def _is_ordinal(column: str, unique_vals: list) -> bool:
    if any(tok in column.lower() for tok in _ORDINAL_TOKENS):
        return True
    val_set = frozenset(str(v).lower().strip() for v in unique_vals)
    for pattern in _ORDINAL_VALUE_SETS:
        if val_set == pattern or val_set.issubset(pattern):
            return True
    return False


def _select_scaler_hint(series: pd.Series) -> str:
    clean = series.dropna()
    if len(clean) < 2:
        return "StandardScaler"
    try:
        skew = abs(float(clean.skew()))
        q1 = clean.quantile(0.25)
        q3 = clean.quantile(0.75)
        iqr = q3 - q1
        has_outliers = iqr > 0 and (
            (clean < q1 - 1.5 * iqr).any() or (clean > q3 + 1.5 * iqr).any()
        )
    except Exception:
        return "StandardScaler"

    if has_outliers:
        return "RobustScaler"
    if skew < 1.0:
        return "StandardScaler"
    if float(clean.min()) >= 0:
        return "MinMaxScaler"
    return "RobustScaler"


def _select_outlier_method(series: pd.Series, n_rows: int) -> str:
    if n_rows < 200:
        return "iqr"
    clean = series.dropna()
    if len(clean) < 4:
        return "iqr"
    try:
        skewness = abs(float(clean.skew()))
        kurt = abs(float(clean.kurtosis()))
        rng = float(clean.max()) - float(clean.min())
        min_abs = abs(float(clean.min()))
    except Exception:
        return "iqr"

    if min_abs > 0 and rng > 1_000 and (float(clean.max()) / max(min_abs, 1e-9)) > 100:
        return "clipping"
    if skewness < 1.0 and kurt < 3.0:
        return "zscore"
    return "iqr"


def _detected_type(column: str, schema: Dict[str, List[str]]) -> str:
    if column in schema.get("numeric", []):
        return "numeric"
    if column in schema.get("datetime", []):
        return "datetime"
    if column in schema.get("text", []):
        return "text"
    return "categorical"


def analyze_columns(
    dataframe: pd.DataFrame,
    schema: Dict[str, List[str]],
    target_column: str,
) -> List[Dict[str, Any]]:
    """
    AI + rule-based column analysis.
    Returns a list of decision records with keys:
      column | detected_type | missing_pct | unique_values | skewness
      suggested_encoding | scaling | outlier_method | action | reason | keep
    """
    results: list[dict[str, Any]] = []
    n_rows = len(dataframe)

    for column in dataframe.columns:
        detected_type = _detected_type(column, schema)
        series = dataframe[column]
        missing_pct = round(float(series.isna().mean() * 100), 2)
        unique_count = int(series.nunique(dropna=True))
        unique_ratio = float(unique_count / max(n_rows, 1))

        # ── Target column ──────────────────────────────────────────────────────
        if column == target_column:
            results.append({
                "column": column,
                "detected_type": "target",
                "missing_pct": missing_pct,
                "unique_values": unique_count,
                "skewness": None,
                "suggested_encoding": "None",
                "scaling": "None",
                "outlier_method": "None",
                "action": "Keep (Target)",
                "reason": "Target column; never modified",
                "keep": True,
            })
            continue

        # ── Compute skewness for numeric ───────────────────────────────────────
        skewness: float | None = None
        if detected_type == "numeric":
            try:
                skewness = round(float(series.skew(skipna=True)), 3)
            except Exception:
                skewness = 0.0

        suggested_encoding = "None"
        scaling = "None"
        outlier_method = "None"
        action = "Keep"
        reason = "Useful feature"
        keep = True

        # ── Drop conditions ────────────────────────────────────────────────────
        if _is_id_like(column):
            action = "Remove (Identifier)"
            reason = "Column name suggests unique identifier"
            keep = False

        elif unique_count <= 1:
            action = "Remove (Constant)"
            reason = "All values are identical – zero variance"
            keep = False

        elif missing_pct > 50:
            action = "Remove (>50% Missing)"
            reason = f"{missing_pct:.1f}% values are missing"
            keep = False

        elif detected_type in ("categorical", "text") and unique_ratio >= 0.95:
            action = "Remove (High Cardinality)"
            reason = f"Unique ratio {unique_ratio:.2f} ≈ row count; likely identifier/free text"
            keep = False

        # ── Encoding decisions (only for kept columns) ─────────────────────────
        elif detected_type in ("categorical", "text"):
            unique_vals = series.dropna().unique().tolist()

            if unique_count == 2:
                suggested_encoding = "LabelEncoding"
                reason = "Binary column → label encode (0/1)"

            elif _is_ordinal(column, unique_vals):
                suggested_encoding = "OrdinalEncoding"
                reason = "Ordinal pattern detected in name or values"

            elif unique_count >= 50 and unique_ratio > 0.15:
                suggested_encoding = "BinaryHashEncoding"
                reason = f"High cardinality ({unique_count} unique) → binary hash reduces dimensionality"

            elif unique_count <= 20:
                suggested_encoding = "OneHotEncoding"
                reason = f"Nominal categorical with {unique_count} unique values → one-hot"

            else:
                suggested_encoding = "BinaryHashEncoding"
                reason = "Moderate-high cardinality → binary hash"

        elif detected_type == "datetime":
            suggested_encoding = "DateFeatureExtraction"
            reason = "DateTime → extract year/month/day components"

        elif detected_type == "numeric":
            scaling = _select_scaler_hint(series)
            outlier_method = _select_outlier_method(series, n_rows)

            if skewness and abs(skewness) > 2:
                reason = f"Skewed numeric (skew={skewness}) → {scaling}, binning candidate"
            else:
                reason = f"Numeric feature → {scaling}"

        results.append({
            "column": column,
            "detected_type": detected_type,
            "missing_pct": missing_pct,
            "unique_values": unique_count,
            "skewness": skewness,
            "suggested_encoding": suggested_encoding,
            "scaling": scaling,
            "outlier_method": outlier_method,
            "action": action,
            "reason": reason,
            "keep": keep,
        })

    return results
