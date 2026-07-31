from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder


# ─── Individual encoders ─────────────────────────────────────────────────────

def _label_encode(df: pd.DataFrame, column: str) -> pd.DataFrame:
    le = LabelEncoder()
    df[column] = le.fit_transform(df[column].astype(str))
    return df


def _ordinal_encode(df: pd.DataFrame, column: str) -> pd.DataFrame:
    oe = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    df[column] = oe.fit_transform(df[[column]].astype(str))
    return df


def _onehot_encode(df: pd.DataFrame, columns: List[str]) -> tuple[pd.DataFrame, List[str]]:
    if not columns:
        return df, []
    enc = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    transformed = enc.fit_transform(df[columns].astype(str))
    new_cols = enc.get_feature_names_out(columns).tolist()
    encoded_df = pd.DataFrame(transformed, columns=new_cols, index=df.index)
    df = pd.concat([df.drop(columns=columns), encoded_df], axis=1)
    return df, new_cols


def _binary_hash_encode(df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, List[str]]:
    """
    Binary (hash-based) encoding: converts each category to a binary bit-vector.
    Handles high-cardinality columns without exploding dimensionality.
    """
    unique_vals = df[column].astype(str).unique()
    n_bits = max(1, int(np.ceil(np.log2(len(unique_vals) + 1))))
    val_to_int = {v: i for i, v in enumerate(sorted(unique_vals))}
    # Use numpy integer array to avoid pandas Series bitwise-shift dtype issues
    int_vals = df[column].astype(str).map(val_to_int).fillna(0).to_numpy(dtype=np.int64)
    new_cols = []
    for bit in range(n_bits):
        col_name = f"{column}_bin_{bit}"
        df[col_name] = ((int_vals >> bit) & 1).astype(int)
        new_cols.append(col_name)
    df = df.drop(columns=[column])
    return df, new_cols


# ─── Public API ───────────────────────────────────────────────────────────────

def encode_categorical_features(
    dataframe: pd.DataFrame,
    categorical_columns: List[str],
    target_column: str,
    encoding_decisions: Dict[str, str] | None = None,
) -> tuple[pd.DataFrame, List[str]]:
    """
    Smart per-column encoding driven by encoding_decisions map.
    Falls back to OneHot when no decision is provided.

    Strategies honored:
        label           → LabelEncoder
        ordinal         → OrdinalEncoder
        onehot          → OneHotEncoder
        binary_hash     → binary bit-vector encoding
        (anything else) → OneHot
    """
    df = dataframe.copy()
    encoding_decisions = encoding_decisions or {}

    columns_to_handle = [
        col for col in categorical_columns
        if col in df.columns and col != target_column
    ]
    if not columns_to_handle:
        return df, []

    all_encoded: list[str] = []
    onehot_queue: list[str] = []

    for column in columns_to_handle:
        strategy = encoding_decisions.get(column, "onehot")

        if strategy in ("label", "binary"):
            df = _label_encode(df, column)
            all_encoded.append(column)

        elif strategy == "ordinal":
            df = _ordinal_encode(df, column)
            all_encoded.append(column)

        elif strategy == "binary_hash":
            df, new_cols = _binary_hash_encode(df, column)
            all_encoded.extend(new_cols)

        elif strategy in ("onehot", "remove_high_cardinality"):
            # remove_high_cardinality columns have been dropped before this step;
            # treat any remaining as onehot
            if column in df.columns:
                onehot_queue.append(column)

        else:
            onehot_queue.append(column)

    # Batch OneHot encoding
    if onehot_queue:
        df, new_cols = _onehot_encode(df, onehot_queue)
        all_encoded.extend(new_cols)

    return df, all_encoded
