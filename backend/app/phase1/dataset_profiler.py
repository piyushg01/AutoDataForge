from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _classify_columns(dataframe: pd.DataFrame) -> Dict[str, List[str]]:
    numeric_columns = dataframe.select_dtypes(include=["number"]).columns.tolist()
    datetime_columns: list[str] = []
    text_columns: list[str] = []
    categorical_columns: list[str] = []

    for column in dataframe.columns:
        if column in numeric_columns:
            continue

        series = dataframe[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_columns.append(column)
            continue

        parsed = pd.to_datetime(series, errors="coerce")
        if float(parsed.notna().mean()) >= 0.8:
            datetime_columns.append(column)
            continue

        unique_ratio = float(series.nunique(dropna=True) / max(len(series), 1))
        avg_length = float(series.astype(str).str.len().mean()) if len(series) else 0.0
        if unique_ratio > 0.6 and avg_length > 18:
            text_columns.append(column)
        else:
            categorical_columns.append(column)

    return {
        "numeric": numeric_columns,
        "categorical": categorical_columns,
        "text": text_columns,
        "datetime": datetime_columns,
    }


def profile_dataset(dataframe: pd.DataFrame) -> Dict[str, Any]:
    schema = _classify_columns(dataframe)

    missing_by_column = {
        column: {
            "count": int(dataframe[column].isna().sum()),
            "pct": round(float(dataframe[column].isna().mean() * 100), 2),
        }
        for column in dataframe.columns
    }

    unique_by_column = {
        column: int(dataframe[column].nunique(dropna=True))
        for column in dataframe.columns
    }

    dtypes = {column: str(dtype) for column, dtype in dataframe.dtypes.items()}

    numeric_summary = dataframe.select_dtypes(include=["number"]).describe().fillna(0).round(4)

    column_summary = []
    for column in dataframe.columns:
        detected_type = "numeric"
        if column in schema["datetime"]:
            detected_type = "datetime"
        elif column in schema["text"]:
            detected_type = "text"
        elif column in schema["categorical"]:
            detected_type = "categorical"

        column_summary.append(
            {
                "column": column,
                "detected_type": detected_type,
                "missing_pct": missing_by_column[column]["pct"],
                "unique_values": unique_by_column[column],
            }
        )

    return {
        "rows": int(len(dataframe)),
        "columns": int(len(dataframe.columns)),
        "schema": schema,
        "missing_by_column": missing_by_column,
        "unique_by_column": unique_by_column,
        "dtypes": dtypes,
        "numeric_summary": numeric_summary.to_dict() if not numeric_summary.empty else {},
        "column_summary": column_summary,
    }
