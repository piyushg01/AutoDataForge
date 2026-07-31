from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def load_dataset(file_name: str, content: bytes) -> pd.DataFrame:
    extension = Path(file_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("Only CSV and Excel files are supported in Phase 1")

    if extension == ".csv":
        return pd.read_csv(BytesIO(content))
    return pd.read_excel(BytesIO(content))
