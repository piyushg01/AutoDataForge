from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def validate_dataset(dataframe: pd.DataFrame) -> Dict[str, Any]:
	missing_total = int(dataframe.isna().sum().sum())
	duplicate_rows = int(dataframe.duplicated().sum())

	numeric = dataframe.select_dtypes(include=["number"])
	finite_ok = True
	if not numeric.empty:
		finite_ok = bool(np.isfinite(numeric.to_numpy()).all())

	return {
		"is_valid": missing_total == 0 and duplicate_rows == 0 and finite_ok,
		"checks": {
			"missing_total": missing_total,
			"duplicate_rows": duplicate_rows,
			"numeric_finite": finite_ok,
		},
	}
