from __future__ import annotations

import pandas as pd


def apply_feature_engineering(
    dataframe: pd.DataFrame,
    target_column: str,
    enabled: bool = True,
) -> tuple[pd.DataFrame, list[str]]:
    if not enabled:
        return dataframe.copy(), []

    df = dataframe.copy()
    created: list[str] = []

    candidate_dates = []
    for column in df.columns:
        if column == target_column:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        parsed = pd.to_datetime(df[column], errors="coerce")
        if float(parsed.notna().mean()) >= 0.8:
            candidate_dates.append((column, parsed))

    for column, parsed in candidate_dates:
        year_col = f"{column}_year"
        month_col = f"{column}_month"
        day_col = f"{column}_day"
        df[year_col] = parsed.dt.year.fillna(0)
        df[month_col] = parsed.dt.month.fillna(0)
        df[day_col] = parsed.dt.day.fillna(0)
        df = df.drop(columns=[column])
        created.extend([year_col, month_col, day_col])

    numeric_cols = [
        column
        for column in df.select_dtypes(include=["number"]).columns.tolist()
        if column != target_column
    ]
    if len(numeric_cols) >= 2:
        a, b = numeric_cols[0], numeric_cols[1]
        ratio_col = f"{a}_to_{b}_ratio"
        df[ratio_col] = df[a] / df[b].replace(0, 1)
        created.append(ratio_col)

    return df, created
