from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.core.config import BASE_DIR
from app.phase1.history_engine import load_pipeline_history


FINGERPRINT_PATH = BASE_DIR / "history" / "dataset_fingerprints.json"


def _build_top_matches(scored: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    unique_by_dataset: Dict[str, Dict[str, Any]] = {}
    fallback_index = 0

    sorted_scored = sorted(scored, key=lambda item: float(item.get("similarity", 0.0)), reverse=True)
    for item in sorted_scored:
        row = item.get("row", {})
        dataset_id = str(row.get("dataset_id") or f"__unknown_{fallback_index}")
        fallback_index += 1

        existing = unique_by_dataset.get(dataset_id)
        if existing is None or float(item.get("similarity", 0.0)) > float(existing.get("similarity", 0.0)):
            unique_by_dataset[dataset_id] = {
                "dataset_id": row.get("dataset_id"),
                "similarity": round(float(item.get("similarity", 0.0)), 4),
                "target_type": (row.get("fingerprint") or {}).get("target_type"),
                "num_rows": (row.get("fingerprint") or {}).get("num_rows"),
                "num_columns": (row.get("fingerprint") or {}).get("num_columns"),
                "missing_percentage": (row.get("fingerprint") or {}).get("missing_percentage"),
                "recommended_pipeline": row.get("best_pipeline", {}),
            }

    top_matches = list(unique_by_dataset.values())
    top_matches.sort(key=lambda item: float(item.get("similarity", 0.0)), reverse=True)
    return top_matches[: max(1, int(limit))]


def load_fingerprints(path: Path = FINGERPRINT_PATH) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []



def _save_fingerprints(rows: List[Dict[str, Any]], path: Path = FINGERPRINT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)



def create_fingerprint(df: pd.DataFrame, target_column: str | None = None) -> Dict[str, Any]:
    feature_df = df.drop(columns=[target_column], errors="ignore") if target_column else df
    numeric_columns = feature_df.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = feature_df.select_dtypes(exclude=["number"]).columns.tolist()
    total_cells = int(df.shape[0] * max(df.shape[1], 1))
    missing_pct = 0.0
    if total_cells > 0:
        missing_pct = round((float(df.isna().sum().sum()) / total_cells) * 100, 4)

    unique_counts = [int(feature_df[col].nunique(dropna=True)) for col in feature_df.columns] if len(feature_df.columns) else []
    avg_unique = round(sum(unique_counts) / max(len(unique_counts), 1), 4)

    target_type = "unknown"
    if target_column and target_column in df.columns:
        target_series = df[target_column]
        if pd.api.types.is_numeric_dtype(target_series):
            target_type = "numeric"
        else:
            target_type = "categorical"

    fingerprint = {
        "num_rows": int(df.shape[0]),
        "num_columns": int(df.shape[1]),
        "num_numeric_columns": len(numeric_columns),
        "num_categorical_columns": len(categorical_columns),
        "missing_percentage": missing_pct,
        "avg_unique_values": avg_unique,
        "target_type": target_type,
    }
    fp_hash = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode("utf-8")).hexdigest()[:12].upper()
    fingerprint["fingerprint_id"] = f"FP-{fp_hash}"
    return fingerprint



def save_fingerprint(
    fingerprint: Dict[str, Any],
    dataset_id: str | None = None,
    best_pipeline: Dict[str, Any] | None = None,
    path: Path = FINGERPRINT_PATH,
) -> Dict[str, Any]:
    rows = load_fingerprints(path)
    record = {
        "dataset_id": dataset_id or fingerprint.get("fingerprint_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fingerprint,
        "best_pipeline": best_pipeline or {},
    }
    rows.append(record)
    rows = rows[-500:]
    _save_fingerprints(rows, path)
    return record



def compute_similarity(f1: Dict[str, Any], f2: Dict[str, Any]) -> float:
    col_diff = abs(int(f1.get("num_columns", 0)) - int(f2.get("num_columns", 0)))
    current_total = max(1, int(f1.get("num_columns", 0)))
    past_total = max(1, int(f2.get("num_columns", 0)))
    current_ratio = float(f1.get("num_numeric_columns", 0)) / current_total
    past_ratio = float(f2.get("num_numeric_columns", 0)) / past_total
    ratio_diff = abs(current_ratio - past_ratio)
    missing_diff = abs(float(f1.get("missing_percentage", 0.0)) - float(f2.get("missing_percentage", 0.0)))

    col_score = max(0.0, 1.0 - (col_diff / max(current_total, past_total, 1)))
    ratio_score = max(0.0, 1.0 - ratio_diff)
    missing_score = max(0.0, 1.0 - (missing_diff / 100.0))
    return round((col_score * 0.4) + (ratio_score * 0.35) + (missing_score * 0.25), 4)



def find_similar_dataset(
    df: pd.DataFrame,
    target_column: str | None = None,
    threshold: float = 0.75,
    path: Path = FINGERPRINT_PATH,
) -> Dict[str, Any]:
    fingerprint = create_fingerprint(df, target_column)
    rows = load_fingerprints(path)
    if not rows:
        return {"found": False, "reason": "no-fingerprints", "similar_dataset_id": None, "recommended_pipeline": {}, "similarity": 0.0, "top_matches": []}

    scored: List[Dict[str, Any]] = []
    for row in rows:
        past_fp = row.get("fingerprint", {})
        score = compute_similarity(fingerprint, past_fp)
        scored.append({"row": row, "similarity": score})

    if not scored:
        return {"found": False, "reason": "no-fingerprints", "similar_dataset_id": None, "recommended_pipeline": {}, "similarity": 0.0, "top_matches": []}

    top_matches = _build_top_matches(scored, limit=5)

    best = sorted(scored, key=lambda item: item["similarity"], reverse=True)[0]
    if best["similarity"] < threshold:
        return {"found": False, "reason": "below-threshold", "similar_dataset_id": None, "recommended_pipeline": {}, "similarity": best["similarity"], "top_matches": top_matches}

    row = best["row"]
    return {
        "found": True,
        "similar_dataset_id": row.get("dataset_id"),
        "similarity": best["similarity"],
        "recommended_pipeline": row.get("best_pipeline", {}),
        "top_matches": top_matches,
    }



def get_similar_pipeline(
    fingerprint: Dict[str, Any],
    threshold: float = 0.75,
    path: Path = FINGERPRINT_PATH,
) -> Dict[str, Any]:
    rows = load_fingerprints(path)
    if not rows:
        return {"found": False, "reason": "no-fingerprints", "similarity": 0.0, "top_matches": []}

    scored: List[Dict[str, Any]] = []
    for row in rows:
        past_fp = row.get("fingerprint", {})
        score = compute_similarity(fingerprint, past_fp)
        scored.append({"row": row, "similarity": score})

    if not scored:
        return {"found": False, "reason": "no-fingerprints", "similarity": 0.0, "top_matches": []}

    top_matches = _build_top_matches(scored, limit=5)

    best_match = sorted(scored, key=lambda item: item["similarity"], reverse=True)[0]
    if best_match["similarity"] < threshold:
        return {"found": False, "reason": "below-threshold", "similarity": best_match["similarity"], "top_matches": top_matches}

    row = best_match["row"]
    similar = {
        "found": True,
        "dataset_id": row.get("dataset_id"),
        "similarity": best_match["similarity"],
        "best_pipeline": row.get("best_pipeline", {}),
        "top_matches": top_matches,
    }
    if not similar.get("found"):
        return similar

    dataset_id = similar.get("dataset_id")
    best_pipeline = similar.get("best_pipeline") or {}
    if best_pipeline:
        return {
            **similar,
            "pipeline_source": "fingerprints",
        }

    history_rows = load_pipeline_history()
    for row in reversed(history_rows):
        if row.get("dataset_id") == dataset_id:
            return {
                **similar,
                "best_pipeline": row.get("pipeline_summary", {}),
                "pipeline_source": "history",
            }

    return {
        **similar,
        "pipeline_source": "unknown",
    }
