from __future__ import annotations

from typing import Dict

import pandas as pd
from sklearn.impute import KNNImputer


def handle_missing_values(dataframe: pd.DataFrame, strategy_by_column: Dict[str, str]) -> pd.DataFrame:
	df = dataframe.copy()

	numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
	if any(strategy_by_column.get(column) == "knn" for column in numeric_columns) and numeric_columns:
		knn = KNNImputer(n_neighbors=3)
		df[numeric_columns] = knn.fit_transform(df[numeric_columns])

	for column in df.columns:
		if not df[column].isna().any():
			continue

		strategy = strategy_by_column.get(column, "mode")
		if pd.api.types.is_numeric_dtype(df[column]):
			if strategy == "mean":
				df[column] = df[column].fillna(df[column].mean())
			elif strategy == "median":
				df[column] = df[column].fillna(df[column].median())
			elif strategy != "knn":
				df[column] = df[column].fillna(0)
		else:
			mode = df[column].mode(dropna=True)
			fill_value = mode.iloc[0] if not mode.empty else "unknown"
			df[column] = df[column].fillna(fill_value)

	return df
