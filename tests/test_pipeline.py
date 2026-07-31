from pathlib import Path
import sys

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
	sys.path.insert(0, str(BACKEND_ROOT))

from app.services.preprocessing_service import run_preprocessing


def test_preprocessing_pipeline_generates_valid_output():
	dataframe = pd.DataFrame(
		{
			"id": [1, 2, 2, 3],
			"age": [20, None, None, 42],
			"country": ["India", "IND", "IND", "Inida"],
			"target": [1, 0, 0, 1],
		}
	)

	result = run_preprocessing(dataframe, target_column="target", problem_type="classification")

	assert result["dataset_id"].startswith("DS-")
	assert Path(result["cleaned_dataset_path"]).exists()
	assert Path(result["report_path"]).exists()
	assert Path(result["pipeline_joblib_path"]).exists()
	assert Path(result["pipeline_code_path"]).exists()
	assert Path(result["selected_features_dataset_path"]).exists()
	assert Path(result["train_test_split_paths"]["x_train"]).exists()
	assert "record_hash" in result["audit"]
