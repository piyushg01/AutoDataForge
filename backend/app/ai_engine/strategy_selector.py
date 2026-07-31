from __future__ import annotations

from typing import Any, Dict


def choose_strategy(profile: Dict[str, Any], issues: Dict[str, Any], target_column: str | None = None) -> Dict[str, Any]:
	missing_strategy: Dict[str, str] = {}
	for column, column_profile in profile.get("column_profiles", {}).items():
		missing_pct = float(column_profile.get("missing_pct", 0))
		dtype_name = str(column_profile.get("dtype", ""))
		if "int" in dtype_name or "float" in dtype_name:
			missing_strategy[column] = "mean" if missing_pct < 5 else "median"
		else:
			missing_strategy[column] = "mode"

	outlier_total = sum(issues.get("outliers_by_column", {}).values())
	outlier_strategy = "iqr_cap" if outlier_total > 0 else "none"

	categorical_strategy = "fuzzy_normalize"
	encoding_strategy = "onehot"

	if target_column and target_column in profile.get("column_profiles", {}):
		target_dtype = str(profile["column_profiles"][target_column].get("dtype", ""))
		scaling_strategy = "standard" if "int" in target_dtype or "float" in target_dtype else "robust"
	else:
		scaling_strategy = "standard"

	return {
		"missing": missing_strategy,
		"duplicates": "drop",
		"outliers": outlier_strategy,
		"categorical": categorical_strategy,
		"encoding": encoding_strategy,
		"scaling": scaling_strategy,
		"feature_selection": "mutual_info_or_variance",
	}
