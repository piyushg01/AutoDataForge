from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from sklearn.model_selection import train_test_split

from app.ai_engine.strategy_selector import choose_strategy
from app.blockchain.audit_logger import append_audit_record, dataframe_hash
from app.cleaning.duplicate_handler import remove_duplicates
from app.cleaning.missing_handler import handle_missing_values
from app.cleaning.outlier_handler import handle_outliers
from app.core.config import get_settings
from app.core.logger import get_logger
from app.detection.issue_detector import detect_issues
from app.feature_engineering.encoder import encode_categoricals
from app.feature_engineering.feature_scaler import scale_features
from app.feature_engineering.feature_selector import select_features
from app.pipeline.pipeline_builder import build_and_save_pipeline
from app.profiling.data_profiler import profile_dataset
from app.validation.validator import validate_dataset


logger = get_logger("preprocessing-service")


def _normalize_categories(dataframe: pd.DataFrame) -> pd.DataFrame:
	df = dataframe.copy()
	for column in df.select_dtypes(exclude=["number"]).columns:
		df[column] = df[column].astype(str).str.strip().str.lower()
	return df


def run_preprocessing(
	dataframe: pd.DataFrame,
	target_column: str,
	problem_type: str,
) -> Dict[str, Any]:
	settings = get_settings()
	dataset_id = f"DS-{uuid.uuid4().hex[:8].upper()}"

	if target_column not in dataframe.columns:
		raise ValueError(f"Target column '{target_column}' not found in dataset")
	if problem_type not in {"classification", "regression"}:
		raise ValueError("problem_type must be either 'classification' or 'regression'")

	profile = profile_dataset(dataframe)
	issues = detect_issues(dataframe)
	strategy = choose_strategy(profile, issues, target_column=target_column)

	cleaned = handle_missing_values(dataframe, strategy["missing"])
	cleaned, duplicates_removed = remove_duplicates(cleaned)
	cleaned = _normalize_categories(cleaned)
	cleaned, outliers_touched = handle_outliers(cleaned, strategy=strategy["outliers"])

	selected, removed_features = select_features(cleaned, target_column=target_column)
	selected_output = settings.output_cleaned / f"{dataset_id}_selected_features.csv"
	selected.to_csv(selected_output, index=False)

	encoded, encoder = encode_categoricals(selected, strategy=strategy["encoding"])
	scaled, scaler = scale_features(encoded, strategy=strategy["scaling"])
	scaled, final_duplicates_removed = remove_duplicates(scaled)

	if target_column not in scaled.columns:
		raise ValueError(
			f"Target column '{target_column}' is missing after preprocessing. "
			"Please verify target naming and transformations."
		)

	x = scaled.drop(columns=[target_column])
	y = scaled[target_column]
	test_size = 0.2
	stratify = None
	if problem_type == "classification":
		class_counts = y.value_counts(dropna=False)
		n_classes = int(y.nunique(dropna=True))
		estimated_test_samples = max(1, int(math.ceil(len(y) * test_size)))
		if (
			n_classes > 1
			and not class_counts.empty
			and int(class_counts.min()) >= 2
			and estimated_test_samples >= n_classes
		):
			stratify = y
	x_train, x_test, y_train, y_test = train_test_split(
		x,
		y,
		test_size=test_size,
		random_state=42,
		stratify=stratify,
	)

	x_train_path = settings.output_cleaned / f"{dataset_id}_X_train.csv"
	x_test_path = settings.output_cleaned / f"{dataset_id}_X_test.csv"
	y_train_path = settings.output_cleaned / f"{dataset_id}_y_train.csv"
	y_test_path = settings.output_cleaned / f"{dataset_id}_y_test.csv"
	x_train.to_csv(x_train_path, index=False)
	x_test.to_csv(x_test_path, index=False)
	y_train.to_frame(name=target_column).to_csv(y_train_path, index=False)
	y_test.to_frame(name=target_column).to_csv(y_test_path, index=False)

	validation = validate_dataset(scaled)

	cleaned_output = settings.output_cleaned / f"{dataset_id}_cleaned.csv"
	scaled.to_csv(cleaned_output, index=False)

	report = {
		"dataset_id": dataset_id,
		"target_column": target_column,
		"problem_type": problem_type,
		"profile_summary": {"rows": profile["rows"], "columns": profile["columns"]},
		"issues": issues,
		"strategy": strategy,
		"results": {
			"missing_values_handled": int(dataframe.isna().sum().sum()),
			"duplicates_removed": duplicates_removed,
			"post_transform_duplicates_removed": final_duplicates_removed,
			"outliers_touched": outliers_touched,
			"categorical_columns_normalized": len(cleaned.select_dtypes(exclude=["number"]).columns),
			"removed_features": removed_features,
			"selected_features": [column for column in selected.columns if column != target_column],
			"final_shape": [int(scaled.shape[0]), int(scaled.shape[1])],
		},
		"validation": validation,
	}

	report_path = settings.output_reports / f"{dataset_id}_report.json"
	with report_path.open("w", encoding="utf-8") as file:
		json.dump(report, file, indent=2)

	pipeline_path = settings.output_pipelines / f"{dataset_id}_pipeline.joblib"
	pipeline_steps: list[tuple[str, object]] = []
	if encoder is not None:
		pipeline_steps.append(("encoder", encoder))
	if scaler is not None:
		pipeline_steps.append(("scaler", scaler))
	if not pipeline_steps:
		pipeline_steps.append(("identity", "passthrough"))

	saved_pipeline = build_and_save_pipeline(pipeline_steps, pipeline_path)
	csv_hash = dataframe_hash(scaled.to_csv(index=False).encode("utf-8"))
	audit = append_audit_record(
		settings.audit_log_path,
		dataset_id=dataset_id,
		dataset_hash=csv_hash,
		transformations=[
			"missing_value_handling",
			"duplicate_removal",
			"category_normalization",
			"outlier_handling",
			"feature_selection",
			"encoding",
			"scaling",
		],
		metadata={
			"pipeline": Path(saved_pipeline["pipeline_joblib_path"]).name,
			"pipeline_code": Path(saved_pipeline["pipeline_code_path"]).name,
			"target_column": target_column,
			"problem_type": problem_type,
		},
	)

	logger.info("Completed preprocessing for dataset_id=%s", dataset_id)
	return {
		"dataset_id": dataset_id,
		"target_column": target_column,
		"problem_type": problem_type,
		"cleaned_dataset_path": str(cleaned_output),
		"selected_features_dataset_path": str(selected_output),
		"train_test_split_paths": {
			"x_train": str(x_train_path),
			"x_test": str(x_test_path),
			"y_train": str(y_train_path),
			"y_test": str(y_test_path),
		},
		"report_path": str(report_path),
		"report": report,
		"pipeline_joblib_path": saved_pipeline["pipeline_joblib_path"],
		"pipeline_code_path": saved_pipeline["pipeline_code_path"],
		"validation": validation,
		"audit": audit,
	}
