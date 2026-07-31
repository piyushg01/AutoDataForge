from __future__ import annotations

import pandas as pd


def remove_duplicates(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, int]:
	duplicate_count = int(dataframe.duplicated().sum())
	cleaned = dataframe.drop_duplicates().reset_index(drop=True)
	return cleaned, duplicate_count
