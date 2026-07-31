from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def dataframe_hash(csv_bytes: bytes) -> str:
	return hashlib.sha256(csv_bytes).hexdigest()


def _record_hash(record: Dict[str, Any], previous_hash: str) -> str:
	payload = json.dumps(record, sort_keys=True).encode("utf-8") + previous_hash.encode("utf-8")
	return hashlib.sha256(payload).hexdigest()


def append_audit_record(
	log_path: Path,
	dataset_id: str,
	dataset_hash: str,
	transformations: List[str],
	metadata: Dict[str, Any],
) -> Dict[str, Any]:
	previous_hash = "GENESIS"
	if log_path.exists():
		with log_path.open("r", encoding="utf-8") as file:
			lines = [line.strip() for line in file.readlines() if line.strip()]
		if lines:
			previous_hash = json.loads(lines[-1]).get("record_hash", "GENESIS")

	record = {
		"dataset_id": dataset_id,
		"dataset_hash": dataset_hash,
		"transformations": transformations,
		"metadata": metadata,
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}
	record["previous_hash"] = previous_hash
	record["record_hash"] = _record_hash(record, previous_hash)

	with log_path.open("a", encoding="utf-8") as file:
		file.write(json.dumps(record) + "\n")

	return record
