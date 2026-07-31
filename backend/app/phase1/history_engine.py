from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import BASE_DIR


HISTORY_PATH = BASE_DIR / "history" / "pipeline_history.json"


def load_pipeline_history(path: Path = HISTORY_PATH) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_pipeline_history(entry: Dict[str, Any], path: Path = HISTORY_PATH, max_items: int = 200) -> Dict[str, Any]:
    rows = load_pipeline_history(path)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    rows.append(payload)
    if len(rows) > max_items:
        rows = rows[-max_items:]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)
    return payload


def suggest_from_history(dataset_stats: Dict[str, Any], path: Path = HISTORY_PATH) -> Dict[str, Any]:
    rows = load_pipeline_history(path)
    if not rows:
        return {"found": False, "reason": "no-history"}

    current_rows = int(dataset_stats.get("rows", 0))
    current_cols = int(dataset_stats.get("columns", 0))
    current_problem = str(dataset_stats.get("problem_type", "")).lower()

    candidates: List[Dict[str, Any]] = []
    for row in rows:
        stats = row.get("dataset_stats", {})
        if current_problem and str(stats.get("problem_type", "")).lower() not in {"", current_problem}:
            continue
        row_gap = abs(int(stats.get("rows", current_rows)) - current_rows)
        col_gap = abs(int(stats.get("columns", current_cols)) - current_cols)
        score = row_gap + (col_gap * 10)
        candidates.append({"distance": score, "entry": row})

    if not candidates:
        return {"found": False, "reason": "no-similar-problem-type"}

    best = sorted(candidates, key=lambda x: x["distance"])[0]["entry"]
    pipeline_summary = best.get("pipeline_summary", {})
    return {
        "found": True,
        "recommended_scaler": pipeline_summary.get("scaler", "none"),
        "recommended_domain": best.get("domain", "general"),
        "reference_timestamp": best.get("timestamp"),
        "reference_score": best.get("model_score"),
    }
