from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def profile_dataset(dataframe: pd.DataFrame) -> Dict[str, Any]:
	profile: Dict[str, Any] = {
		"rows": int(len(dataframe)),
		"columns": int(len(dataframe.columns)),
		"column_profiles": {},
	}

	numeric_columns = dataframe.select_dtypes(include=["number"]).columns.tolist()
	categorical_columns = dataframe.select_dtypes(exclude=["number"]).columns.tolist()

	profile["numeric_columns"] = numeric_columns
	profile["categorical_columns"] = categorical_columns

	for column in dataframe.columns:
		series = dataframe[column]
		dtype_name = str(series.dtype)
		missing_pct = float(series.isna().mean() * 100)
		unique_count = int(series.nunique(dropna=True))

		column_info: Dict[str, Any] = {
			"dtype": dtype_name,
			"missing_pct": round(missing_pct, 2),
			"unique_count": unique_count,
		}

		if pd.api.types.is_numeric_dtype(series):
			column_info.update(
				{
					"mean": float(series.mean(skipna=True)) if series.notna().any() else None,
					"median": float(series.median(skipna=True)) if series.notna().any() else None,
					"variance": float(series.var(skipna=True)) if series.notna().any() else None,
					"skew": float(series.skew(skipna=True)) if series.notna().any() else None,
				}
			)

		profile["column_profiles"][column] = column_info

	return profile
