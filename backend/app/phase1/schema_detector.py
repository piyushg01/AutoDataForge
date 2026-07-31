from __future__ import annotations

from typing import Dict, List

import pandas as pd


def detect_schema(dataframe: pd.DataFrame) -> Dict[str, List[str]]:
    numeric_cols = dataframe.select_dtypes(include=["number"]).columns.tolist()
    datetime_cols: list[str] = []
    text_cols: list[str] = []
    categorical_cols: list[str] = []

    for column in dataframe.columns:
        if column in numeric_cols:
            continue

        series = dataframe[column]

        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(column)
            continue

        parsed = pd.to_datetime(series, errors="coerce")
        parse_ratio = float(parsed.notna().mean()) if len(series) else 0.0
        if parse_ratio >= 0.8:
            datetime_cols.append(column)
            continue

        unique_ratio = float(series.nunique(dropna=True) / max(len(series), 1))
        avg_length = float(series.astype(str).str.len().mean()) if len(series) else 0.0
        if unique_ratio > 0.6 and avg_length > 20:
            text_cols.append(column)
        else:
            categorical_cols.append(column)

    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "text": text_cols,
        "datetime": datetime_cols,
    }
