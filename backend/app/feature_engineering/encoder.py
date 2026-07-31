from __future__ import annotations

from typing import Literal

import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder


EncodingName = Literal["onehot", "label"]


def encode_categoricals(dataframe: pd.DataFrame, strategy: EncodingName = "onehot") -> tuple[pd.DataFrame, object | None]:
	df = dataframe.copy()
	categorical_columns = df.select_dtypes(exclude=["number"]).columns.tolist()
	if not categorical_columns:
		return df, None

	if strategy == "label":
		encoders: dict[str, LabelEncoder] = {}
		for column in categorical_columns:
			encoder = LabelEncoder()
			df[column] = encoder.fit_transform(df[column].astype(str))
			encoders[column] = encoder
		return df, encoders

	onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
	encoded_matrix = onehot.fit_transform(df[categorical_columns].astype(str))
	encoded_columns = onehot.get_feature_names_out(categorical_columns)
	encoded_df = pd.DataFrame(encoded_matrix, columns=encoded_columns, index=df.index)
	df = pd.concat([df.drop(columns=categorical_columns), encoded_df], axis=1)
	return df, onehot
