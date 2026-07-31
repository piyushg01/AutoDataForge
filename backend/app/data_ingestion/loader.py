from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}


def load_dataset(file_name: str, content: bytes) -> pd.DataFrame:
	extension = Path(file_name).suffix.lower()
	if extension not in SUPPORTED_EXTENSIONS:
		raise ValueError(f"Unsupported file type: {extension}")

	if extension == ".csv":
		return pd.read_csv(BytesIO(content))
	if extension in {".xlsx", ".xls"}:
		return pd.read_excel(BytesIO(content))
	return pd.read_json(BytesIO(content))


def load_dataset_from_path(path: str | Path) -> pd.DataFrame:
	dataset_path = Path(path)
	if not dataset_path.exists():
		raise FileNotFoundError(f"Dataset not found: {dataset_path}")

	extension = dataset_path.suffix.lower()
	if extension == ".csv":
		return pd.read_csv(dataset_path)
	if extension in {".xlsx", ".xls"}:
		return pd.read_excel(dataset_path)
	if extension == ".json":
		return pd.read_json(dataset_path)
	raise ValueError(f"Unsupported file type: {extension}")
