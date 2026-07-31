from __future__ import annotations

import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, mutual_info_classif, mutual_info_regression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from app.core.config import get_settings
from app.phase1.history_engine import suggest_from_history


def generate_pipeline_variants() -> List[Dict[str, Any]]:
    variants: List[Dict[str, Any]] = []
    index = 1
    for scaler in ["StandardScaler", "MinMaxScaler", "RobustScaler"]:
        for encoding in ["onehot", "label"]:
            for feature_selection in [True, False]:
                for outlier_removal in [True, False]:
                    variants.append({
                        "id": index,
                        "name": f"pipeline_{index}",
                        "scaler": scaler,
                        "encoding": encoding,
                        "feature_selection": feature_selection,
                        "outlier_removal": outlier_removal,
                    })
                    index += 1
    return variants


def _normalize_recommended_pipeline(recommended_pipeline: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not recommended_pipeline:
        return None
    scaler = recommended_pipeline.get("scaler")
    encoding = recommended_pipeline.get("encoding")
    feature_selection = recommended_pipeline.get("feature_selection")
    outlier_removal = recommended_pipeline.get("outlier_removal")
    if scaler is None or encoding is None or feature_selection is None or outlier_removal is None:
        return None
    return {
        "id": recommended_pipeline.get("id", 0),
        "name": recommended_pipeline.get("name", "recommended_pipeline"),
        "scaler": scaler,
        "encoding": encoding,
        "feature_selection": bool(feature_selection),
        "outlier_removal": bool(outlier_removal),
    }


def _prioritize_recommended_pipeline(
    variants: List[Dict[str, Any]],
    recommended_pipeline: Dict[str, Any] | None,
) -> tuple[List[Dict[str, Any]], bool]:
    normalized = _normalize_recommended_pipeline(recommended_pipeline)
    if not normalized:
        return variants, False

    def _same_variant(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
        return (
            left.get("scaler") == right.get("scaler")
            and left.get("encoding") == right.get("encoding")
            and bool(left.get("feature_selection")) == bool(right.get("feature_selection"))
            and bool(left.get("outlier_removal")) == bool(right.get("outlier_removal"))
        )

    remaining = [variant for variant in variants if not _same_variant(variant, normalized)]
    return [normalized, *remaining], True


def _bias_variants_from_history(
    variants: List[Dict[str, Any]],
    df: pd.DataFrame,
    problem_type: str,
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    history_hint = suggest_from_history({
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "problem_type": problem_type,
    })
    if not history_hint.get("found"):
        return variants, history_hint

    recommended_scaler = history_hint.get("recommended_scaler")
    if not recommended_scaler or recommended_scaler == "none":
        return variants, history_hint

    prioritized = [v for v in variants if v.get("scaler") == recommended_scaler]
    remaining = [v for v in variants if v.get("scaler") != recommended_scaler]
    return prioritized + remaining, history_hint


def _apply_outlier_treatment(x_df: pd.DataFrame) -> pd.DataFrame:
    out = x_df.copy()
    numeric_cols = out.select_dtypes(include=["number"]).columns.tolist()
    for col in numeric_cols:
        series = out[col]
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower = q1 - (1.5 * iqr)
        upper = q3 + (1.5 * iqr)
        out[col] = series.clip(lower=lower, upper=upper)
    return out


def _encode_features(x_df: pd.DataFrame, strategy: str) -> pd.DataFrame:
    out = x_df.copy()
    categorical_cols = out.select_dtypes(exclude=["number"]).columns.tolist()

    if not categorical_cols:
        return out

    if strategy == "label":
        for col in categorical_cols:
            encoder = LabelEncoder()
            out[col] = encoder.fit_transform(out[col].astype(str))
        return out

    # onehot default
    return pd.get_dummies(out, columns=categorical_cols, drop_first=False)


def _apply_feature_selection(x_arr: np.ndarray, y_arr: np.ndarray, problem_type: str) -> np.ndarray:
    if x_arr.shape[1] <= 2:
        return x_arr
    k = max(2, min(x_arr.shape[1], int(np.sqrt(x_arr.shape[1]) * 2)))
    if problem_type == "classification":
        selector = SelectKBest(score_func=mutual_info_classif, k=k)
    else:
        selector = SelectKBest(score_func=mutual_info_regression, k=k)
    return selector.fit_transform(x_arr, y_arr)


def _prepare_matrix(df: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, np.ndarray] | None:
    if target_column not in df.columns:
        return None
    y = df[target_column]
    x = df.drop(columns=[target_column]).copy()
    if x.empty:
        return None
    x = x.replace([np.inf, -np.inf], np.nan)
    x_arr = x
    y_arr = y.values
    return x_arr, y_arr


def _scaler(name: str):
    if name == "RobustScaler":
        return RobustScaler()
    if name == "MinMaxScaler":
        return MinMaxScaler()
    return StandardScaler()


def evaluate_pipeline(df: pd.DataFrame, target_column: str, problem_type: str, variant: Dict[str, Any]) -> Dict[str, Any]:
    prepared = _prepare_matrix(df, target_column)
    if prepared is None:
        return {"variant": variant["name"], "config": variant, "score": -1.0, "status": "skipped"}

    x_df, y_arr = prepared
    if len(x_df) < 4:
        return {"variant": variant["name"], "config": variant, "score": -1.0, "status": "insufficient_rows"}

    if variant.get("outlier_removal"):
        x_df = _apply_outlier_treatment(x_df)

    x_df = _encode_features(x_df, variant.get("encoding", "onehot"))
    x_df = x_df.replace([np.inf, -np.inf], np.nan)
    x_arr = SimpleImputer(strategy="median").fit_transform(x_df)

    scaler = _scaler(variant["scaler"])
    x_scaled = scaler.fit_transform(x_arr)

    if variant.get("feature_selection"):
        try:
            x_scaled = _apply_feature_selection(x_scaled, y_arr, problem_type)
        except Exception:
            pass

    x_train, x_test, y_train, y_test = train_test_split(x_scaled, y_arr, test_size=0.25, random_state=42)

    try:
        if problem_type == "classification":
            model_lr = LogisticRegression(max_iter=500)
            model_rf = RandomForestClassifier(n_estimators=150, random_state=42)
            model_lr.fit(x_train, y_train)
            model_rf.fit(x_train, y_train)
            pred_lr = model_lr.predict(x_test)
            pred_rf = model_rf.predict(x_test)
            score_lr = accuracy_score(y_test, pred_lr)
            score_rf = accuracy_score(y_test, pred_rf)
            if score_rf >= score_lr:
                score = float(score_rf)
                selected_model = "RandomForestClassifier"
            else:
                score = float(score_lr)
                selected_model = "LogisticRegression"
            metric = "accuracy"
        else:
            model_rf = RandomForestRegressor(n_estimators=150, random_state=42)
            model_rf.fit(x_train, y_train)
            pred_rf = model_rf.predict(x_test)
            score = float(r2_score(y_test, pred_rf))
            selected_model = "RandomForestRegressor"
            metric = "r2"
        return {
            "variant": variant["name"],
            "config": variant,
            "metric": metric,
            "model": selected_model,
            "score": score,
            "status": "ok",
        }
    except Exception as exc:
        return {
            "variant": variant["name"],
            "config": variant,
            "score": -1.0,
            "status": f"error:{exc}",
        }


def select_best_pipeline(
    df: pd.DataFrame,
    target_column: str,
    problem_type: str,
    recommended_pipeline: Dict[str, Any] | None = None,
    similar_dataset_id: str | None = None,
) -> Dict[str, Any]:
    variants = generate_pipeline_variants()
    attrs_recommended = df.attrs.get("suggested_pipeline") if hasattr(df, "attrs") else None
    attrs_similar_dataset_id = df.attrs.get("similar_dataset_id") if hasattr(df, "attrs") else None
    effective_recommended = recommended_pipeline or attrs_recommended
    effective_similar_dataset_id = similar_dataset_id or attrs_similar_dataset_id

    variants, similarity_used = _prioritize_recommended_pipeline(variants, effective_recommended)
    variants, history_hint = _bias_variants_from_history(variants, df, problem_type)
    results = [evaluate_pipeline(df, target_column, problem_type, v) for v in variants]
    valid = [r for r in results if r.get("status") == "ok"]
    if not valid:
        payload = {
            "selected": None,
            "results": results,
            "reason": "no-valid-variant",
            "history_bias": history_hint,
            "similarity_used": similarity_used,
            "similar_dataset_id": effective_similar_dataset_id,
        }
        settings = get_settings()
        output_path = settings.output_reports.parent / "optimization_result.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)
        return payload

    best = sorted(valid, key=lambda x: x.get("score", -1), reverse=True)[0]
    message = f"{best.get('variant')} selected because {best.get('metric')} highest ({best.get('score'):.4f})"
    payload = {
        "selected": best,
        "results": results,
        "reason": "best-score",
        "explanation": message,
        "history_bias": history_hint,
        "similarity_used": similarity_used,
        "similar_dataset_id": effective_similar_dataset_id,
    }
    settings = get_settings()
    output_path = settings.output_reports.parent / "optimization_result.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
    return payload
