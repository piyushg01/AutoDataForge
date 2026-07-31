from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import BASE_DIR


AUDIT_PATH = BASE_DIR / "audit" / "audit_log.json"


def _load(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _hash_record(record: Dict[str, Any], prev_hash: str) -> str:
    payload = json.dumps(record, sort_keys=True).encode("utf-8") + prev_hash.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def log_step(action: str, details: Dict[str, Any], path: Path = AUDIT_PATH) -> Dict[str, Any]:
    rows = _load(path)
    prev_hash = rows[-1].get("current_hash", "GENESIS") if rows else "GENESIS"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": action,
        "action": action,
        "details": details,
        "prev_hash": prev_hash,
    }
    entry["current_hash"] = _hash_record(entry, prev_hash)

    rows.append(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)
    return entry


def load_audit(path: Path = AUDIT_PATH, limit: int = 300) -> List[Dict[str, Any]]:
    rows = _load(path)
    if limit <= 0:
        return rows
    return rows[-limit:]
