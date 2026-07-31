from __future__ import annotations

from typing import List

import pandas as pd
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression


def _drop_id_like_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
	id_like = [column for column in dataframe.columns if column.lower().endswith("id") or column.lower() == "id"]
	return dataframe.drop(columns=id_like, errors="ignore")


def select_features(
	dataframe: pd.DataFrame,
	target_column: str | None = None,
	correlation_threshold: float = 0.95,
) -> tuple[pd.DataFrame, List[str]]:
	df = _drop_id_like_columns(dataframe.copy())
	if target_column and target_column in dataframe.columns and target_column not in df.columns:
		df[target_column] = dataframe[target_column]

	removed: list[str] = []

	constant_columns = [column for column in df.columns if df[column].nunique(dropna=False) <= 1]
	if constant_columns:
		df = df.drop(columns=constant_columns)
		removed.extend(constant_columns)

	feature_frame = df.drop(columns=[target_column], errors="ignore") if target_column else df
	numeric = feature_frame.select_dtypes(include=["number"])
	if not numeric.empty:
		correlation = numeric.corr().abs()
		upper = correlation.where(~correlation.index.to_series().duplicated(), other=0)
		to_drop = []
		for col in upper.columns:
			if any(upper[col] > correlation_threshold):
				to_drop.append(col)
		if to_drop:
			df = df.drop(columns=list(set(to_drop)), errors="ignore")
			removed.extend(list(set(to_drop)))

	if target_column and target_column in df.columns:
		y = df[target_column]
		x = df.drop(columns=[target_column])
		x_num = x.select_dtypes(include=["number"]) 
		if not x_num.empty:
			if y.nunique() <= 20 and str(y.dtype) not in {"float64", "float32"}:
				scores = mutual_info_classif(x_num.fillna(0), y)
			else:
				scores = mutual_info_regression(x_num.fillna(0), y)

			score_map = dict(zip(x_num.columns, scores))
			low_info = [column for column, score in score_map.items() if score <= 0.0001]
			if low_info:
				safe_low_info = [column for column in low_info if column != target_column]
				df = df.drop(columns=safe_low_info, errors="ignore")
				removed.extend(safe_low_info)

	if target_column and target_column in dataframe.columns and target_column not in df.columns:
		df[target_column] = dataframe[target_column]

	return df, sorted(set(removed))
