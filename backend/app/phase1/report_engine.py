from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _compute_quality_score(
    missing_pct: float,
    outliers_capped: int,
    dropped_columns_count: int,
    row_count: int,
) -> float:
    outlier_penalty = 0.0
    if row_count > 0:
        outlier_penalty = min(25.0, (outliers_capped / max(row_count, 1)) * 100)
    dropped_penalty = min(20.0, dropped_columns_count * 4.0)
    score = 100.0 - (missing_pct * 0.6) - outlier_penalty - dropped_penalty
    return round(_clamp(score), 2)


def _compute_pipeline_confidence(best_score: float | None, second_best_score: float | None) -> float:
    if best_score is None:
        return 0.0
    if second_best_score is None:
        return round(_clamp(best_score * 100), 2)
    margin = max(0.0, best_score - second_best_score)
    confidence = (best_score * 70.0) + (margin * 100.0)
    return round(_clamp(confidence), 2)


def _compute_risk_level(missing_pct: float, outliers_capped: int, dropped_columns_count: int) -> str:
    if missing_pct >= 25 or outliers_capped >= 20 or dropped_columns_count >= 4:
        return "high"
    if missing_pct >= 10 or outliers_capped >= 8 or dropped_columns_count >= 2:
        return "medium"
    return "low"


def build_cleaning_report(
    rows_before: int,
    rows_after: int,
    duplicates_removed: int,
    outliers_capped: int,
    dropped_columns: List[str],
    selected_features: List[str],
    scaler_name: str,
    encoding_decisions: Dict[str, str],
    missing_actions: Dict[str, str],
    created_features: List[str],
) -> Dict[str, Any]:
    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicates_removed": duplicates_removed,
        "outliers_capped": outliers_capped,
        "dropped_columns": dropped_columns,
        "selected_features": selected_features,
        "scaler": scaler_name,
        "encoding_decisions": encoding_decisions,
        "missing_actions": missing_actions,
        "created_features": created_features,
    }



def generate_report(
    *,
    missing_pct: float,
    outliers_capped: int,
    dropped_columns: List[str],
    optimization_result: Dict[str, Any],
    explanations: List[Dict[str, Any]],
    domain: str,
    reproducible: bool,
    row_count: int,
) -> Dict[str, Any]:
    valid_results = [
        row for row in optimization_result.get("results", [])
        if row.get("status") == "ok" and isinstance(row.get("score"), (int, float))
    ]
    sorted_results = sorted(valid_results, key=lambda x: x.get("score", -1), reverse=True)
    best = sorted_results[0] if sorted_results else (optimization_result.get("selected") or {})
    second = sorted_results[1] if len(sorted_results) > 1 else None
    best_cfg = best.get("config", {}) if isinstance(best, dict) else {}

    best_score = best.get("score") if isinstance(best, dict) else None
    second_best_score = second.get("score") if isinstance(second, dict) else None
    history_bias = optimization_result.get("history_bias", {})

    report = {
        "dataset_quality_score": _compute_quality_score(
            missing_pct=missing_pct,
            outliers_capped=outliers_capped,
            dropped_columns_count=len(dropped_columns),
            row_count=row_count,
        ),
        "pipeline_confidence": _compute_pipeline_confidence(best_score, second_best_score),
        "risk_level": _compute_risk_level(missing_pct, outliers_capped, len(dropped_columns)),
        "selected_pipeline": best.get("variant") if isinstance(best, dict) else None,
        "selected_scaler": best_cfg.get("scaler"),
        "selected_encoding": best_cfg.get("encoding"),
        "history_bias_used": bool(history_bias.get("found")),
        "number_of_variants_tested": len(optimization_result.get("results", [])),
        "best_score": best_score,
        "explanations_used": len(explanations),
        "domain": domain,
        "reproducible": reproducible,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return report



def save_report(report: Dict[str, Any], output_path: Path) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
    return str(output_path)
