from __future__ import annotations

import pandas as pd


def handle_outliers(dataframe: pd.DataFrame, strategy: str = "iqr_cap") -> tuple[pd.DataFrame, int]:
	if strategy == "none":
		return dataframe.copy(), 0

	df = dataframe.copy()
	touched = 0
	for column in df.select_dtypes(include=["number"]).columns:
		series = df[column]
		q1 = series.quantile(0.25)
		q3 = series.quantile(0.75)
		iqr = q3 - q1
		if iqr == 0:
			continue

		lower = q1 - 1.5 * iqr
		upper = q3 + 1.5 * iqr

		if strategy == "iqr_filter":
			before = len(df)
			df = df[(df[column] >= lower) & (df[column] <= upper)]
			touched += before - len(df)
		else:
			mask = (df[column] < lower) | (df[column] > upper)
			touched += int(mask.sum())
			df[column] = df[column].clip(lower=lower, upper=upper)

	return df.reset_index(drop=True), touched
