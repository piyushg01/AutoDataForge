from __future__ import annotations

from typing import Dict

import pandas as pd

# Ordinal-indicator tokens in column names
_ORDINAL_TOKENS = [
    "rank", "level", "grade", "stage", "tier", "class",
    "priority", "severity", "order", "degree",
]

# Known ordinal value patterns (lowercase)
_ORDINAL_VALUE_SETS: list[frozenset] = [
    frozenset({"low", "medium", "high"}),
    frozenset({"low", "medium", "high", "very high"}),
    frozenset({"small", "medium", "large"}),
    frozenset({"bad", "average", "good", "excellent"}),
    frozenset({"never", "rarely", "sometimes", "often", "always"}),
    frozenset({"none", "mild", "moderate", "severe"}),
]


def _is_ordinal(column: str, unique_vals: list) -> bool:
    """Heuristic: check name tokens or value-set patterns."""
    lowered = column.lower()
    if any(tok in lowered for tok in _ORDINAL_TOKENS):
        return True
    val_set = frozenset(str(v).lower().strip() for v in unique_vals)
    for pattern in _ORDINAL_VALUE_SETS:
        if val_set == pattern or val_set.issubset(pattern):
            return True
    return False


def suggest_encodings(dataframe: pd.DataFrame, target_column: str) -> Dict[str, str]:
    """
    AI rule-based encoding selection per categorical/text column.
    Returns mapping: column → encoding_strategy
    Strategies: label | ordinal | onehot | binary_hash | remove_high_cardinality
    """
    decisions: dict[str, str] = {}
    n_rows = max(len(dataframe), 1)

    non_numeric = dataframe.select_dtypes(exclude=["number"]).columns.tolist()
    for column in non_numeric:
        if column == target_column:
            continue

        unique_count = int(dataframe[column].nunique(dropna=True))
        unique_ratio = float(unique_count / n_rows)
        unique_vals = dataframe[column].dropna().unique().tolist()

        # 1. Exactly 2 unique values → binary label encoding
        if unique_count == 2:
            decisions[column] = "label"

        # 2. Near-unique / identifier text → remove
        elif unique_ratio >= 0.95:
            decisions[column] = "remove_high_cardinality"

        # 3. Ordinal patterns (name + value heuristics)
        elif _is_ordinal(column, unique_vals):
            decisions[column] = "ordinal"

        # 4. High cardinality but not identifier (50+ unique, >15% of rows)
        elif unique_count >= 50 and unique_ratio > 0.15:
            decisions[column] = "binary_hash"

        # 5. Moderate cardinality (up to 20 unique) → OneHot
        elif unique_count <= 20:
            decisions[column] = "onehot"

        # 6. Anything else (21–49 unique, low ratio) → binary hash
        else:
            decisions[column] = "binary_hash"

    return decisions
