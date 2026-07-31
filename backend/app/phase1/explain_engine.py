from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import BASE_DIR


EXPLAIN_PATH = BASE_DIR / "history" / "explanations.json"


def _load(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)


def log_decision(column: str, action: str, reason: str, path: Path = EXPLAIN_PATH) -> Dict[str, Any]:
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "column": column,
        "action": action,
        "reason": reason,
    }
    rows = _load(path)
    rows.append(row)
    _save(path, rows)
    return row


def get_latest_decisions(limit: int = 500, path: Path = EXPLAIN_PATH) -> List[Dict[str, Any]]:
    rows = _load(path)
    if limit <= 0:
        return rows
    return rows[-limit:]
