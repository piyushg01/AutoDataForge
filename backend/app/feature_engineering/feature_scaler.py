from __future__ import annotations

from typing import Literal

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler


ScalerName = Literal["standard", "minmax", "robust"]


def scale_features(dataframe: pd.DataFrame, strategy: ScalerName = "standard") -> tuple[pd.DataFrame, object | None]:
	df = dataframe.copy()
	numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
	if not numeric_columns:
		return df, None

	if strategy == "minmax":
		scaler = MinMaxScaler()
	elif strategy == "robust":
		scaler = RobustScaler()
	else:
		scaler = StandardScaler()

	df[numeric_columns] = scaler.fit_transform(df[numeric_columns])
	return df, scaler
