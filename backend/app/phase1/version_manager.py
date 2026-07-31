from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

from app.core.config import BASE_DIR


VERSIONS_DIR = BASE_DIR / "versions"


def save_version(name: str, df: pd.DataFrame, versions_dir: Path = VERSIONS_DIR) -> str:
    versions_dir.mkdir(parents=True, exist_ok=True)
    clean_name = name.replace(" ", "_").lower().strip()
    out = versions_dir / f"{clean_name}.csv"
    df.to_csv(out, index=False)
    return str(out)


def load_version(name: str, versions_dir: Path = VERSIONS_DIR) -> pd.DataFrame:
    clean_name = name.replace(" ", "_").lower().strip()
    path = versions_dir / f"{clean_name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Version not found: {name}")
    return pd.read_csv(path)


def list_versions(versions_dir: Path = VERSIONS_DIR) -> List[str]:
    if not versions_dir.exists():
        return []
    return sorted([p.name for p in versions_dir.glob("*.csv")])
