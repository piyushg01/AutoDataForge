from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict

import pandas as pd


def _detect_outliers_iqr(series: pd.Series) -> int:
	clean = series.dropna()
	if clean.empty:
		return 0
	q1 = clean.quantile(0.25)
	q3 = clean.quantile(0.75)
	iqr = q3 - q1
	if iqr == 0:
		return 0
	lower = q1 - 1.5 * iqr
	upper = q3 + 1.5 * iqr
	return int(((series < lower) | (series > upper)).sum())


def _categorical_inconsistencies(series: pd.Series) -> Dict[str, str]:
	mapping: Dict[str, str] = {}
	values = [str(v).strip() for v in series.dropna().astype(str).unique()]
	canonical_values: list[str] = []

	for value in values:
		normalized = value.lower()
		matched = None
		for canonical in canonical_values:
			score = SequenceMatcher(None, normalized, canonical).ratio()
			if score >= 0.85:
				matched = canonical
				break
		if matched is None:
			canonical_values.append(normalized)
			mapping[value] = value
		else:
			mapping[value] = matched

	return mapping


def detect_issues(dataframe: pd.DataFrame) -> Dict[str, Any]:
	issues: Dict[str, Any] = {
		"missing_by_column": dataframe.isna().sum().to_dict(),
		"total_missing": int(dataframe.isna().sum().sum()),
		"duplicate_rows": int(dataframe.duplicated().sum()),
		"outliers_by_column": {},
		"categorical_inconsistencies": {},
	}

	for column in dataframe.select_dtypes(include=["number"]).columns:
		issues["outliers_by_column"][column] = _detect_outliers_iqr(dataframe[column])

	for column in dataframe.select_dtypes(exclude=["number"]).columns:
		mapping = _categorical_inconsistencies(dataframe[column])
		changed = {source: target for source, target in mapping.items() if source.lower() != target.lower()}
		if changed:
			issues["categorical_inconsistencies"][column] = changed

	return issues
