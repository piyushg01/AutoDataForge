"""
Dimensionality Reduction module.

Implements:
  - PCA  (Principal Component Analysis)   → use when many features (>20)
  - LDA  (Linear Discriminant Analysis)   → use for classification tasks
  - CCA  (placeholder – use when multiple related datasets)

AI rules:
  - n_features > 20 + regression/unknown  → PCA
  - n_features > 15 + classification       → LDA
  - Both can be force-enabled via parameters
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis


# ─── public helpers ─────────────────────────────────────────────────────────────

def _decide_method(
    n_features: int,
    problem_type: str,
    force_method: str | None,
) -> str | None:
    if force_method and force_method in ("pca", "lda", "none"):
        return None if force_method == "none" else force_method

    if problem_type == "classification" and n_features > 15:
        return "lda"
    if n_features > 20:
        return "pca"
    return None


def _apply_pca(
    feature_df: pd.DataFrame,
    variance_explained: float = 0.95,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """Reduce dimensions, keeping components that explain variance_explained of variance."""
    numeric_cols = feature_df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric = [c for c in feature_df.columns if c not in numeric_cols]

    if len(numeric_cols) < 2:
        return feature_df, {"method": "pca", "skipped": True, "reason": "too_few_numeric_cols"}

    X = feature_df[numeric_cols].values
    # Replace NaN/inf
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    n_components = min(len(numeric_cols), len(feature_df) - 1, 50)
    pca = PCA(n_components=n_components, svd_solver="auto")
    try:
        transformed = pca.fit_transform(X)
    except Exception as exc:
        return feature_df, {"method": "pca", "skipped": True, "reason": str(exc)}

    # Keep components accounting for variance_explained
    cum_var = np.cumsum(pca.explained_variance_ratio_)
    n_keep = int(np.searchsorted(cum_var, variance_explained) + 1)
    n_keep = max(1, min(n_keep, n_components))

    pca_cols = [f"pca_{i + 1}" for i in range(n_keep)]
    pca_df = pd.DataFrame(transformed[:, :n_keep], columns=pca_cols, index=feature_df.index)

    out = pd.concat([feature_df[non_numeric].reset_index(drop=True), pca_df.reset_index(drop=True)], axis=1)
    report = {
        "method": "pca",
        "original_numeric_cols": len(numeric_cols),
        "components_kept": n_keep,
        "variance_explained": float(cum_var[n_keep - 1]),
        "component_names": pca_cols,
    }
    return out, report


def _apply_lda(
    feature_df: pd.DataFrame,
    target_series: pd.Series,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """LDA reduction for classification; n_components = min(n_classes-1, n_features)."""
    numeric_cols = feature_df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric = [c for c in feature_df.columns if c not in numeric_cols]

    if len(numeric_cols) < 2:
        return feature_df, {"method": "lda", "skipped": True, "reason": "too_few_numeric_cols"}

    X = feature_df[numeric_cols].values
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    n_classes = int(target_series.nunique())
    n_components = min(n_classes - 1, len(numeric_cols), len(feature_df) - 1)

    if n_components < 1:
        return feature_df, {"method": "lda", "skipped": True, "reason": "not_enough_classes"}

    lda = LinearDiscriminantAnalysis(n_components=n_components)
    try:
        transformed = lda.fit_transform(X, target_series.values)
    except Exception as exc:
        return feature_df, {"method": "lda", "skipped": True, "reason": str(exc)}

    lda_cols = [f"lda_{i + 1}" for i in range(n_components)]
    lda_df = pd.DataFrame(transformed, columns=lda_cols, index=feature_df.index)

    out = pd.concat([feature_df[non_numeric].reset_index(drop=True), lda_df.reset_index(drop=True)], axis=1)
    report = {
        "method": "lda",
        "original_numeric_cols": len(numeric_cols),
        "components_kept": n_components,
        "classes": n_classes,
        "component_names": lda_cols,
    }
    return out, report


# ─── main entry point ───────────────────────────────────────────────────────────

def apply_dimensionality_reduction(
    dataframe: pd.DataFrame,
    target_column: str,
    problem_type: str = "classification",
    force_method: str | None = None,
    pca_variance: float = 0.95,
    enabled: bool = False,
) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply dimensionality reduction if enabled and beneficial.

    Args:
        dataframe     : Full DataFrame including target column
        target_column : Column to exclude from reduction
        problem_type  : 'classification' or 'regression'
        force_method  : 'pca' | 'lda' | 'none' | None (auto)
        pca_variance  : Variance to retain for PCA (default 0.95)
        enabled       : Gate; False → skip

    Returns:
        (processed_df, report_dict)
    """
    if not enabled:
        return dataframe.copy(), {"skipped": True, "reason": "disabled"}

    target_series = dataframe[target_column].copy()
    feature_df = dataframe.drop(columns=[target_column]).copy()

    n_features = len(feature_df.select_dtypes(include=["number"]).columns)
    method = _decide_method(n_features, problem_type, force_method)

    if method is None:
        result_df = pd.concat([feature_df, target_series], axis=1)
        return result_df, {"skipped": True, "reason": f"n_features={n_features}_below_threshold"}

    if method == "lda":
        reduced_features, report = _apply_lda(feature_df, target_series)
    else:
        reduced_features, report = _apply_pca(feature_df, variance_explained=pca_variance)

    if report.get("skipped"):
        result_df = pd.concat([feature_df, target_series], axis=1)
        return result_df, report

    result_df = pd.concat(
        [reduced_features.reset_index(drop=True), target_series.reset_index(drop=True)],
        axis=1,
    )
    return result_df, report
