from __future__ import annotations

from typing import Any, Dict, Iterable


VALID_DOMAINS = {"general", "finance", "healthcare", "sales", "iot"}


def detect_domain(columns: Iterable[str], user_domain: str | None = None) -> str:
    if user_domain and user_domain.lower() in VALID_DOMAINS:
        return user_domain.lower()

    names = " ".join([str(c).lower() for c in columns])
    if any(k in names for k in ["revenue", "balance", "loan", "interest", "credit", "amount"]):
        return "finance"
    if any(k in names for k in ["patient", "diagnosis", "heart", "blood", "hospital", "clinical"]):
        return "healthcare"
    if any(k in names for k in ["sales", "sku", "customer", "order", "invoice", "price"]):
        return "sales"
    if any(k in names for k in ["sensor", "device", "telemetry", "temperature", "humidity", "signal"]):
        return "iot"
    return "general"


def apply_domain_rules(domain: str) -> Dict[str, Any]:
    domain = (domain or "general").lower()
    if domain == "finance":
        return {
            "skip_outlier_capping": True,
            "missing_bias": "median",
            "note": "Finance domain keeps extreme values for anomaly/risk signals.",
        }
    if domain == "healthcare":
        return {
            "skip_outlier_capping": False,
            "missing_bias": "median",
            "note": "Healthcare domain uses conservative imputation defaults.",
        }
    if domain == "sales":
        return {
            "skip_outlier_capping": False,
            "missing_bias": "mode",
            "note": "Sales domain favors mode/median handling for sparse categorical fields.",
        }
    if domain == "iot":
        return {
            "skip_outlier_capping": False,
            "missing_bias": "ffill",
            "note": "IoT domain can prefer smoothing/forward-fill behavior for streams.",
        }
    return {
        "skip_outlier_capping": False,
        "missing_bias": "auto",
        "note": "General domain default rules.",
    }
