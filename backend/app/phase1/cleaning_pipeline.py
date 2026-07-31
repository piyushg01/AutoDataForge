from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from app.core.config import get_settings
from app.phase1.column_analyzer import analyze_columns
from app.phase1.dataset_profiler import profile_dataset
from app.phase1.dim_reduction import apply_dimensionality_reduction
from app.phase1.domain_engine import apply_domain_rules, detect_domain
from app.phase1.discretizer import apply_discretization
from app.phase1.duplicate_remover import remove_duplicates
from app.phase1.encoder import encode_categorical_features
from app.phase1.encoding_selector import suggest_encodings
from app.phase1.explain_engine import log_decision
from app.phase1.feature_engineering import apply_feature_engineering
from app.phase1.feature_generator import create_feature, suggest_features
from app.phase1.feature_selector import remove_unnecessary_columns, run_feature_selection
from app.phase1.history_engine import save_pipeline_history, suggest_from_history
from app.phase1.missing_value_handler import handle_missing_values
from app.phase1.outlier_handler import handle_outliers
from app.phase1.pipeline_optimizer import select_best_pipeline
from app.phase1.report_engine import build_cleaning_report, generate_report, save_report
from app.phase1.scaler import scale_features_per_column
from app.phase1.similarity_engine import create_fingerprint, find_similar_dataset, get_similar_pipeline, save_fingerprint
from app.phase1.version_manager import list_versions, save_version
from app.phase1.audit_logger import log_step


OUTPUT_FILE_NAME = "cleaned_dataset.csv"
PIPELINE_PROGRESS: Dict[str, Any] = {
    "step_name": "idle",
    "percent": 0,
    "history": [],
}


def update_progress(step_name: str, percent: int) -> Dict[str, Any]:
    bounded_percent = max(0, min(100, int(percent)))
    entry = {
        "step_name": step_name,
        "percent": bounded_percent,
    }

    if bounded_percent == 0:
        PIPELINE_PROGRESS["history"] = [entry]
    else:
        history = PIPELINE_PROGRESS.get("history", [])
        history.append(entry)
        PIPELINE_PROGRESS["history"] = history[-100:]

    PIPELINE_PROGRESS["step_name"] = step_name
    PIPELINE_PROGRESS["percent"] = bounded_percent

    return {
        "step_name": PIPELINE_PROGRESS["step_name"],
        "percent": PIPELINE_PROGRESS["percent"],
        "history": list(PIPELINE_PROGRESS.get("history", [])),
    }


def get_progress() -> Dict[str, Any]:
    return {
        "step_name": PIPELINE_PROGRESS.get("step_name", "idle"),
        "percent": int(PIPELINE_PROGRESS.get("percent", 0)),
        "history": list(PIPELINE_PROGRESS.get("history", [])),
    }


def _read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return fallback


def _build_chart_data(dataframe: pd.DataFrame) -> Dict[str, Any]:
    numeric_columns = dataframe.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = dataframe.select_dtypes(exclude=["number"]).columns.tolist()

    histograms = []
    boxplots = []
    for column in numeric_columns[:10]:
        clean = dataframe[column].dropna()
        histograms.append({"column": column, "values": clean.tolist()})
        # Boxplot stats: min, q1, median, q3, max
        if len(clean) >= 4:
            boxplots.append({
                "column": column,
                "min": float(clean.min()),
                "q1": float(clean.quantile(0.25)),
                "median": float(clean.median()),
                "q3": float(clean.quantile(0.75)),
                "max": float(clean.max()),
                "mean": float(clean.mean()),
                "std": float(clean.std()),
            })

    category_bars = []
    for column in categorical_columns[:10]:
        top = dataframe[column].astype(str).value_counts(dropna=False).head(15)
        category_bars.append({
            "column": column,
            "labels": [str(idx) for idx in top.index.tolist()],
            "values": [int(v) for v in top.values.tolist()],
        })

    correlation = []
    corr_columns = []
    if numeric_columns:
        corr = dataframe[numeric_columns].corr().replace([np.inf, -np.inf], 0).fillna(0)
        corr_columns = corr.columns.tolist()
        correlation = corr.values.round(4).tolist()

    # Skewness for each numeric column
    skewness = {}
    for col in numeric_columns:
        try:
            skewness[col] = round(float(dataframe[col].skew()), 3)
        except Exception:
            skewness[col] = 0.0

    return {
        "numeric_histograms": histograms,
        "numeric_boxplots": boxplots,
        "categorical_bars": category_bars,
        "correlation_heatmap": {
            "columns": corr_columns,
            "matrix": correlation,
        },
        "skewness": skewness,
    }


def build_dashboard_payload(dataframe: pd.DataFrame) -> Dict[str, Any]:
    profile = profile_dataset(dataframe)
    charts = _build_chart_data(dataframe)
    preview = dataframe.head(30).fillna("").to_dict(orient="records")
    return {
        "profile": profile,
        "charts": charts,
        "preview": preview,
        "columns": dataframe.columns.tolist(),
    }


def run_phase1_cleaning(
    dataframe: pd.DataFrame,
    target_column_name: str,
    problem_type: str,
    confirmed_drop_columns: List[str] | None = None,
    enable_feature_engineering: bool = True,
    enable_discretization: bool = False,
    enable_dim_reduction: bool = False,
    dim_reduction_method: str | None = None,
    domain: str | None = None,
    enable_optimizer: bool = True,
    enable_history: bool = True,
    enable_feature_suggestions: bool = True,
) -> Dict[str, Any]:
    """
    Full Phase-1 AI-driven preprocessing pipeline.

        Integrated orchestration order:
            1. Load dataset
            2. Profile dataset
            3. Domain detection
            4. Column analysis
            5. History suggestion
            6. Similarity detection
            7. Cleaning
            8. Encoding
            9. Scaling
         10. Feature selection
         11. Optimizer
         12. Apply best pipeline
         13. Save
         14. Report
         15. Export
    """
    if target_column_name not in dataframe.columns:
        raise ValueError(f"Target column '{target_column_name}' not found in dataset")
    if problem_type not in {"classification", "regression"}:
        raise ValueError("problem_type must be 'classification' or 'regression'")

    settings = get_settings()
    rows_before = int(len(dataframe))
    explanations: list[dict[str, Any]] = []
    versions_saved: list[str] = []
    raw_snapshot = dataframe.copy()

    update_progress("load dataset", 0)

    log_step("load_dataset", {"rows": int(dataframe.shape[0]), "columns": int(dataframe.shape[1])})

    # ── Step 1: Profile ────────────────────────────────────────────────────────
    initial_profile = profile_dataset(dataframe)
    log_step("profile_dataset", {
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "numeric_columns": len(initial_profile.get("schema", {}).get("numeric", [])),
        "categorical_columns": len(initial_profile.get("schema", {}).get("categorical", [])),
    })
    update_progress("profiling", 10)

    # ── Step 2: Domain-aware rules ─────────────────────────────────────────────
    detected_domain = detect_domain(dataframe.columns.tolist(), user_domain=domain)
    domain_rules = apply_domain_rules(detected_domain)
    log_step("domain_rules", {"domain": detected_domain, "rules": domain_rules})
    update_progress("domain detection", 20)

    # ── Step 3: AI column analysis ─────────────────────────────────────────────
    processing_suggestions = analyze_columns(
        dataframe,
        schema=initial_profile["schema"],
        target_column=target_column_name,
    )
    log_step("column_analysis", {"suggestion_count": len(processing_suggestions)})
    update_progress("column analysis", 30)

    # ── Step 4: History suggestions ────────────────────────────────────────────
    dataset_fingerprint = create_fingerprint(dataframe, target_column_name)
    history_suggestion = {"found": False, "reason": "history-disabled"}
    if enable_history:
        history_suggestion = suggest_from_history({
            "rows": int(dataframe.shape[0]),
            "columns": int(dataframe.shape[1]),
            "problem_type": problem_type,
        })

    # ── Step 5: Similarity detection ──────────────────────────────────────────
    similar_dataset_match = find_similar_dataset(dataframe, target_column_name)
    similar_pipeline_hint = get_similar_pipeline(dataset_fingerprint)
    if enable_history:
        log_step("history_suggestions", {
            **history_suggestion,
            "similarity_match": similar_dataset_match,
            "similar_dataset": similar_pipeline_hint,
        })

    # ── Step 6: Feature suggestions ────────────────────────────────────────────
    feature_suggestions = suggest_features(dataframe, target_column_name) if enable_feature_suggestions else []
    log_step("feature_suggestions", {"enabled": enable_feature_suggestions, "count": len(feature_suggestions)})

    # ── Step 7: Preprocessing decisions ────────────────────────────────────────
    initial_encoding_decisions = suggest_encodings(dataframe, target_column=target_column_name)
    preprocessing_decisions = {
        "domain_rules": domain_rules,
        "history": history_suggestion,
        "similarity_match": similar_dataset_match,
        "similar_pipeline": similar_pipeline_hint,
        "encoding_decisions": initial_encoding_decisions,
        "feature_suggestions": feature_suggestions,
    }
    log_step("preprocessing_decisions", {
        "encoding_columns": len(initial_encoding_decisions),
        "feature_suggestions": len(feature_suggestions),
    })

    # ── Step 8: Apply preprocessing (existing flow) ───────────────────────────
    # Missing value handling
    df, missing_report = handle_missing_values(dataframe, target_column=target_column_name)
    after_missing_snapshot = df.copy()
    log_step("missing_value_handling", {"actions": missing_report.get("missing_actions", {})})
    update_progress("missing handling", 40)

    # Remove duplicates
    df, duplicates_removed = remove_duplicates(df)
    log_step("remove_duplicates", {"duplicates_removed": int(duplicates_removed)})

    # Outlier handling (domain-aware)
    schema_after_missing = profile_dataset(df)["schema"]
    if domain_rules.get("skip_outlier_capping", False):
        outlier_report = {}
        outliers_capped = 0
        log_step("outlier_handling", {"skipped": True, "reason": "domain_rule"})
    else:
        df, outlier_report = handle_outliers(
            df,
            numeric_columns=schema_after_missing.get("numeric", []),
            target_column=target_column_name,
        )
        outliers_capped = sum(v["outliers_found"] for v in outlier_report.values())
        log_step("outlier_handling", {"outliers_capped": int(outliers_capped), "columns": len(outlier_report)})

    # Drop unnecessary columns
    suggested_drop = missing_report.get("suggested_drop_columns", [])
    confirmed_drop_columns = confirmed_drop_columns or []
    all_drop_candidates = sorted(set(suggested_drop + confirmed_drop_columns))

    df, feature_selection_report = remove_unnecessary_columns(
        df,
        target_column=target_column_name,
        suggested_drop_columns=all_drop_candidates,
    )
    log_step("drop_columns", {"count": len(feature_selection_report.get("dropped_columns", []))})

    # Feature engineering
    df, created_features = apply_feature_engineering(
        df,
        target_column=target_column_name,
        enabled=enable_feature_engineering,
    )
    log_step("feature_engineering", {"enabled": enable_feature_engineering, "created": created_features})

    # Apply one suggested generated feature (if available)
    if feature_suggestions:
        try:
            df = create_feature(df, feature_suggestions[0])
            created_features.append(feature_suggestions[0].get("feature"))
            log_step("feature_generation", {"applied": feature_suggestions[0]})
        except Exception as exc:
            log_step("feature_generation", {"error": str(exc)})

    # Discretization (optional)
    df, discretization_report = apply_discretization(
        df,
        target_column=target_column_name,
        enabled=enable_discretization,
    )
    log_step("discretization", {"enabled": enable_discretization, "count": len(discretization_report.get("discretized", {}))})

    # Smart encoding
    encoding_decisions = suggest_encodings(df, target_column=target_column_name)

    # Drop columns flagged for removal from encoding stage
    high_cardinality = [col for col, dec in encoding_decisions.items() if dec == "remove_high_cardinality"]
    if high_cardinality:
        df = df.drop(columns=high_cardinality, errors="ignore")
    after_encoding_snapshot = df.copy()
    log_step("encoding", {"columns": len(encoding_decisions), "high_cardinality_dropped": high_cardinality})

    schema_before_encoding = profile_dataset(df)["schema"]
    cat_cols = schema_before_encoding.get("categorical", []) + schema_before_encoding.get("text", [])
    df, _encoded_columns = encode_categorical_features(
        df,
        categorical_columns=cat_cols,
        target_column=target_column_name,
        encoding_decisions=encoding_decisions,
    )
    update_progress("encoding", 50)

    # Per-column scaling
    df, scaler_decisions = scale_features_per_column(
        df,
        target_column=target_column_name,
        outlier_report=outlier_report,
    )
    # Pick representative scaler name for summary
    if scaler_decisions:
        from collections import Counter
        scaler_name = Counter(scaler_decisions.values()).most_common(1)[0][0]
    else:
        scaler_name = "none"
    if history_suggestion.get("recommended_scaler") and scaler_name == "none":
        scaler_name = history_suggestion.get("recommended_scaler")
    after_scaling_snapshot = df.copy()
    log_step("scaling", {"scaler": scaler_name, "decisions": scaler_decisions})
    update_progress("scaling", 60)

    # Multi-method feature selection (after encoding + scaling)
    df, adv_selection_report = run_feature_selection(
        df,
        target_column=target_column_name,
        problem_type=problem_type,
    )
    log_step("feature_selection", {
        "mutual_info_dropped": len(adv_selection_report.get("mutual_info_dropped", [])),
        "embedded_dropped": len(adv_selection_report.get("embedded_dropped", [])),
    })

    # ── Step 9: Pipeline optimization ──────────────────────────────────────────
    optimization_result = {"selected": None, "results": [], "reason": "optimizer-disabled"}
    if enable_optimizer:
        optimizer_input = df.copy()
        recommended_pipeline = similar_dataset_match.get("recommended_pipeline") or None
        similar_dataset_id = similar_dataset_match.get("similar_dataset_id")
        if similar_dataset_match.get("found") and similar_dataset_match.get("recommended_pipeline"):
            optimizer_input.attrs["suggested_pipeline"] = similar_dataset_match.get("recommended_pipeline")
            optimizer_input.attrs["similar_dataset_id"] = similar_dataset_id
            explanations.append(log_decision(
                "__similarity__",
                "pipeline_reuse",
                "Using pipeline from similar dataset",
            ))
        optimization_result = select_best_pipeline(
            optimizer_input,
            target_column_name,
            problem_type,
            recommended_pipeline=recommended_pipeline,
            similar_dataset_id=similar_dataset_id,
        )
        log_step("pipeline_optimization", {
            "selected": optimization_result.get("selected"),
            "reason": optimization_result.get("reason"),
            "similarity_match": similar_dataset_match,
            "history_bias": history_suggestion,
        })
        selected_variant = (optimization_result.get("selected") or {}).get("variant")
        explanations.append(log_decision(
            "__optimizer__",
            "optimizer_result",
            f"reason={optimization_result.get('reason')} selected={selected_variant}",
        ))
        if optimization_result.get("explanation"):
            explanations.append(log_decision(
                "__optimizer__",
                "pipeline_selection",
                optimization_result.get("explanation"),
            ))
    update_progress("optimization", 70)

    # Dimensionality reduction (optional)
    df, dim_report = apply_dimensionality_reduction(
        df,
        target_column=target_column_name,
        problem_type=problem_type,
        force_method=dim_reduction_method,
        enabled=enable_dim_reduction,
    )
    log_step("dimensionality_reduction", {"enabled": enable_dim_reduction, "result": dim_report})

    # ── Step 10: Apply best pipeline ───────────────────────────────────────────
    selected_opt = optimization_result.get("selected") or {}
    selected_cfg = selected_opt.get("config") or {}

    selected_scaler = selected_opt.get("scaler") or selected_cfg.get("scaler")
    selected_encoding = selected_opt.get("encoding") or selected_cfg.get("encoding")
    selected_feature_selection = selected_opt.get("feature_selection")
    if selected_feature_selection is None:
        selected_feature_selection = selected_cfg.get("feature_selection", False)
    selected_outlier_removal = selected_opt.get("outlier_removal")
    if selected_outlier_removal is None:
        selected_outlier_removal = selected_cfg.get("outlier_removal", False)

    applied_steps: Dict[str, Any] = {}

    if bool(selected_outlier_removal):
        schema_for_outliers = profile_dataset(df).get("schema", {})
        numeric_for_outliers = schema_for_outliers.get("numeric", [])
        df, enforced_outlier_report = handle_outliers(
            df,
            numeric_columns=numeric_for_outliers,
            target_column=target_column_name,
        )
        if enforced_outlier_report:
            outlier_report = enforced_outlier_report
            outliers_capped = sum(v.get("outliers_found", 0) for v in outlier_report.values())
        applied_steps["outlier_handling"] = {
            "enabled": True,
            "columns": len(enforced_outlier_report),
            "outliers_capped": int(outliers_capped),
        }

    if selected_encoding in {"onehot", "label", "ordinal", "binary_hash", "binary"}:
        schema_for_encoding = profile_dataset(df).get("schema", {})
        categorical_for_encoding = [
            col for col in (schema_for_encoding.get("categorical", []) + schema_for_encoding.get("text", []))
            if col in df.columns and col != target_column_name
        ]
        if categorical_for_encoding:
            enforced_encoding_decisions = {col: selected_encoding for col in categorical_for_encoding}
            df, enforced_encoded_columns = encode_categorical_features(
                df,
                categorical_columns=categorical_for_encoding,
                target_column=target_column_name,
                encoding_decisions=enforced_encoding_decisions,
            )
            encoding_decisions.update(enforced_encoding_decisions)
            applied_steps["encoding"] = {
                "strategy": selected_encoding,
                "columns": len(categorical_for_encoding),
                "generated_features": len(enforced_encoded_columns),
            }

    if selected_scaler in {"StandardScaler", "MinMaxScaler", "RobustScaler", "Normalizer"}:
        df, enforced_scaler_decisions = scale_features_per_column(
            df,
            target_column=target_column_name,
            outlier_report=outlier_report,
        )
        if enforced_scaler_decisions:
            scaler_decisions = enforced_scaler_decisions
            from collections import Counter
            scaler_name = Counter(scaler_decisions.values()).most_common(1)[0][0]
        applied_steps["scaling"] = {
            "requested": selected_scaler,
            "applied_columns": len(enforced_scaler_decisions),
        }

    if bool(selected_feature_selection):
        df, enforced_selection_report = run_feature_selection(
            df,
            target_column=target_column_name,
            problem_type=problem_type,
        )
        adv_selection_report = enforced_selection_report
        applied_steps["feature_selection"] = {
            "enabled": True,
            "mutual_info_dropped": len(adv_selection_report.get("mutual_info_dropped", [])),
            "embedded_dropped": len(adv_selection_report.get("embedded_dropped", [])),
        }

    log_step("apply_best_pipeline", {
        "selected_pipeline": selected_opt.get("variant"),
        "applied": bool(selected_cfg),
        "settings": {
            "scaler": selected_scaler,
            "encoding": selected_encoding,
            "feature_selection": bool(selected_feature_selection),
            "outlier_removal": bool(selected_outlier_removal),
        },
        "applied_steps": applied_steps,
    })
    explanations.append(log_decision(
        "__optimizer__",
        "apply_best_pipeline",
        f"applied settings: scaler={selected_scaler}, encoding={selected_encoding}, feature_selection={bool(selected_feature_selection)}, outlier_removal={bool(selected_outlier_removal)}",
    ))

    # Reorder columns – target last
    target_series = df[target_column_name]
    feature_df = df.drop(columns=[target_column_name])
    final_df = pd.concat([feature_df, target_series], axis=1)
    final_snapshot = final_df.copy()

    # ── Step 11: Save dataset versions ─────────────────────────────────────────
    versions_saved.append(save_version("raw", raw_snapshot))
    versions_saved.append(save_version("after_missing", after_missing_snapshot))
    versions_saved.append(save_version("after_encoding", after_encoding_snapshot))
    versions_saved.append(save_version("after_scaling", after_scaling_snapshot))
    versions_saved.append(save_version("final", final_snapshot))
    update_progress("version save", 80)

    # Aggregate dropped columns
    all_dropped = sorted(set(
        feature_selection_report.get("dropped_columns", [])
        + high_cardinality
        + adv_selection_report.get("low_variance_dropped", [])
        + adv_selection_report.get("high_correlation_dropped", [])
        + adv_selection_report.get("mutual_info_dropped", [])
        + adv_selection_report.get("embedded_dropped", [])
    ))

    report = build_cleaning_report(
        rows_before=rows_before,
        rows_after=int(len(final_df)),
        duplicates_removed=duplicates_removed,
        outliers_capped=outliers_capped,
        dropped_columns=all_dropped,
        selected_features=[col for col in final_df.columns if col != target_column_name],
        scaler_name=scaler_name,
        encoding_decisions=encoding_decisions,
        missing_actions=missing_report.get("missing_actions", {}),
        created_features=created_features,
    )

    cleaned_preview = final_df.head(30).fillna("").to_dict(orient="records")

    # ── Step 12: Audit logging ─────────────────────────────────────────────────
    log_step("audit_logging", {
        "stage": "completed",
        "version_files": len(versions_saved),
        "rows": int(final_df.shape[0]),
        "columns": int(final_df.shape[1]),
    })

    # ── Step 13: Explainable decision logging ─────────────────────────────────
    for col, strategy in report.get("missing_actions", {}).items():
        explanations.append(log_decision(col, f"missing:{strategy}", "missing value strategy chosen by AI rules"))
    for col, strategy in encoding_decisions.items():
        explanations.append(log_decision(col, f"encoding:{strategy}", "encoding chosen by cardinality/type heuristics"))
    for col, scaler in scaler_decisions.items():
        explanations.append(log_decision(col, f"scaling:{scaler}", "scaler chosen from skewness/outlier profile"))
    for col, info in outlier_report.items():
        explanations.append(log_decision(col, f"outlier:{info.get('method')}", "outlier method chosen from distribution analysis"))
    for col in adv_selection_report.get("mutual_info_dropped", []):
        explanations.append(log_decision(col, "feature_selection:mutual_info_drop", "feature dropped by mutual information threshold"))
    for col in adv_selection_report.get("embedded_dropped", []):
        explanations.append(log_decision(col, "feature_selection:embedded_drop", "feature dropped by embedded model importance"))
    for col in adv_selection_report.get("high_correlation_dropped", []):
        explanations.append(log_decision(col, "feature_selection:correlation_drop", "feature dropped due to high correlation"))
    for col in adv_selection_report.get("low_variance_dropped", []):
        explanations.append(log_decision(col, "feature_selection:low_variance_drop", "feature dropped due to low variance"))
    explanations.append(log_decision("__domain__", f"domain:{detected_domain}", domain_rules.get("note", "domain rule applied")))

    # ── Step 14: Final pipeline report ─────────────────────────────────────────
    dataset_stats = {
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "problem_type": problem_type,
        "rows_after": int(final_df.shape[0]),
        "columns_after": int(final_df.shape[1]),
    }
    missing_cells = int(dataframe.isna().sum().sum())
    total_cells = int(dataframe.shape[0] * max(dataframe.shape[1], 1))
    missing_pct = 0.0
    if total_cells > 0:
        missing_pct = round((float(missing_cells) / total_cells) * 100, 2)

    history_bias = optimization_result.get("history_bias") or history_suggestion
    similarity_used = optimization_result.get("similarity_used")
    if similarity_used is None:
        similarity_used = bool(similar_dataset_match.get("found"))
    optimization_for_report = {
        **optimization_result,
        "history_bias": history_bias,
        "similarity_used": similarity_used,
        "dataset_stats": dataset_stats,
        "missing_stats": {
            "missing_cells": missing_cells,
            "total_cells": total_cells,
            "missing_pct": missing_pct,
        },
        "outlier_stats": {
            "outliers_capped": outliers_capped,
            "outlier_columns": len(outlier_report),
        },
    }

    final_report = generate_report(
        missing_pct=missing_pct,
        outliers_capped=outliers_capped,
        dropped_columns=all_dropped,
        optimization_result=optimization_for_report,
        explanations=explanations,
        domain=detected_domain,
        reproducible=bool(versions_saved),
        row_count=int(final_df.shape[0]),
    )
    final_report_path = save_report(
        final_report,
        settings.output_reports.parent / "final_report.json",
    )
    update_progress("report generation", 90)

    # ── Step 15: Save cleaned dataset export ───────────────────────────────────
    output_path = settings.output_cleaned / OUTPUT_FILE_NAME
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    log_step("save_final_dataset", {
        "path": str(output_path),
        "rows": int(final_df.shape[0]),
        "columns": int(final_df.shape[1]),
    })

    # ── Step 16: Persist history for self-learning ─────────────────────────────
    saved_history = save_pipeline_history({
        "dataset_id": dataset_fingerprint.get("fingerprint_id"),
        "domain": detected_domain,
        "dataset_stats": {
            "rows": int(dataframe.shape[0]),
            "columns": int(dataframe.shape[1]),
            "problem_type": problem_type,
        },
        "pipeline_summary": {
            "selected_pipeline": selected_opt.get("variant"),
            "scaler": selected_cfg.get("scaler"),
            "encoding": selected_cfg.get("encoding"),
            "feature_selection": selected_cfg.get("feature_selection"),
            "outlier_removal": selected_cfg.get("outlier_removal"),
            "outliers_capped": outliers_capped,
            "dropped_columns": all_dropped,
        },
        "model_score": (optimization_result.get("selected") or {}).get("score"),
    })

    # ── Step 17: Save fingerprint ──────────────────────────────────────────────
    saved_fingerprint = save_fingerprint(
        fingerprint={
            **dataset_fingerprint,
            "domain": detected_domain,
            "score": selected_opt.get("score"),
        },
        dataset_id=dataset_fingerprint.get("fingerprint_id"),
        best_pipeline=selected_opt,
    )

    optimization_summary = {
        "best_pipeline": selected_opt.get("variant"),
        "score": selected_opt.get("score"),
        "tested_pipelines": len(optimization_result.get("results", [])),
        "chosen_scaler": selected_cfg.get("scaler"),
        "chosen_encoding": selected_cfg.get("encoding"),
    }

    backend_root = settings.output_reports.parent.parent

    backend_files = {
        "optimization_result": _read_json_file(settings.output_reports.parent / "optimization_result.json", {}),
        "pipeline_history": _read_json_file(backend_root / "history" / "pipeline_history.json", []),
        "dataset_fingerprints": _read_json_file(backend_root / "history" / "dataset_fingerprints.json", []),
        "audit_log": _read_json_file(backend_root / "audit" / "audit_log.json", []),
        "final_report": _read_json_file(settings.output_reports.parent / "final_report.json", {}),
    }

    final_progress = update_progress("done", 100)

    return {
        "cleaned_dataset_path": str(output_path),
        "target_column": target_column_name,
        "problem_type": problem_type,
        "rows": int(final_df.shape[0]),
        "columns": int(final_df.shape[1]),
        "duplicates_removed": duplicates_removed,
        "outliers_capped": outliers_capped,
        "outlier_report": {k: v for k, v in outlier_report.items()},
        "dropped_columns": all_dropped,
        "selected_features": report["selected_features"],
        "encoded_feature_count": len(_encoded_columns),
        "scaler": scaler_name,
        "scaler_decisions": scaler_decisions,
        "missing_actions": report["missing_actions"],
        "processing_suggestions": processing_suggestions,
        "encoding_decisions": encoding_decisions,
        "preprocessing_decisions": preprocessing_decisions,
        "discretization": discretization_report,
        "dim_reduction": dim_report,
        "feature_selection": {
            "mutual_info_scores": adv_selection_report.get("mutual_info_scores", {}),
            "feature_importances": adv_selection_report.get("feature_importances", {}),
            "dropped": {
                "correlation": adv_selection_report.get("high_correlation_dropped", []),
                "mutual_info": adv_selection_report.get("mutual_info_dropped", []),
                "low_importance": adv_selection_report.get("embedded_dropped", []),
            },
        },
        "domain": {
            "selected": domain,
            "detected": detected_domain,
            "rules": domain_rules,
        },
        "history": {
            "suggestions": history_suggestion,
            "similar_pipeline": similar_pipeline_hint,
            "saved": saved_history,
        },
        "similarity": {
            "match": similar_dataset_match,
            "pipeline": similar_pipeline_hint,
        },
        "dataset_fingerprint": saved_fingerprint,
        "optimization": optimization_result,
        "optimizer_result": optimization_result,
        "best_pipeline": optimization_summary["best_pipeline"],
        "score": optimization_summary["score"],
        "tested_pipelines": optimization_summary["tested_pipelines"],
        "chosen_scaler": optimization_summary["chosen_scaler"],
        "chosen_encoding": optimization_summary["chosen_encoding"],
        "explanations": explanations[-200:],
        "feature_generation": {
            "suggestions": feature_suggestions,
            "applied": created_features,
        },
        "versions": {
            "saved_paths": versions_saved,
            "available": list_versions(),
        },
        "audit": {
            "log_file": "audit/audit_log.json",
        },
        "audit_log": backend_files.get("audit_log", []),
        "final_report": final_report,
        "final_report_path": final_report_path,
        "backend_files": backend_files,
        "report": report,
        "cleaned_preview": cleaned_preview,
        "progress": final_progress,
        "download_urls": {},
    }
