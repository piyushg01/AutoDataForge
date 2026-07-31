from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.phase1.cleaning_pipeline import (
    OUTPUT_FILE_NAME,
    build_dashboard_payload,
    run_phase1_cleaning,
)
from app.phase1.column_analyzer import analyze_columns
from app.phase1.data_loader import load_dataset
from app.phase1.dataset_profiler import profile_dataset


router = APIRouter()
settings = get_settings()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/profile")
async def profile_uploaded_dataset(file: UploadFile = File(...)) -> dict:
    try:
        content = await file.read()
        dataframe = load_dataset(file.filename, content)
        return build_dashboard_payload(dataframe)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze")
async def analyze_uploaded_dataset(
    file: UploadFile = File(...),
    target_column_name: str = Form(...),
) -> dict:
    try:
        content = await file.read()
        dataframe = load_dataset(file.filename, content)
        profile = profile_dataset(dataframe)
        suggestions = analyze_columns(
            dataframe,
            schema=profile["schema"],
            target_column=target_column_name,
        )
        return {
            "target_column": target_column_name,
            "processing_suggestions": suggestions,
            "profile": profile,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/clean")
async def clean_uploaded_dataset(
    file: UploadFile = File(...),
    target_column_name: str = Form(...),
    problem_type: str = Form(...),
    confirmed_drop_columns_json: str | None = Form(default=None),
    enable_feature_engineering: bool = Form(default=True),
    enable_discretization: bool = Form(default=False),
    enable_dim_reduction: bool = Form(default=False),
    dim_reduction_method: str | None = Form(default=None),
    domain: str | None = Form(default=None),
    enable_optimizer: bool = Form(default=True),
    enable_history: bool = Form(default=True),
    enable_feature_suggestions: bool = Form(default=True),
) -> dict:
    try:
        confirmed_drop_columns = []
        if confirmed_drop_columns_json:
            confirmed_drop_columns = json.loads(confirmed_drop_columns_json)
            if not isinstance(confirmed_drop_columns, list):
                raise ValueError("confirmed_drop_columns_json must be a JSON array of column names")

        content = await file.read()
        dataframe = load_dataset(file.filename, content)

        result = run_phase1_cleaning(
            dataframe,
            target_column_name=target_column_name,
            problem_type=problem_type,
            confirmed_drop_columns=confirmed_drop_columns,
            enable_feature_engineering=enable_feature_engineering,
            enable_discretization=enable_discretization,
            enable_dim_reduction=enable_dim_reduction,
            dim_reduction_method=dim_reduction_method if dim_reduction_method else None,
            domain=domain,
            enable_optimizer=enable_optimizer,
            enable_history=enable_history,
            enable_feature_suggestions=enable_feature_suggestions,
        )

        result["download_urls"] = {
            "cleaned": f"{settings.api_prefix}/download/phase1/cleaned",
        }
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/download/phase1/cleaned")
def download_phase1_cleaned_dataset():
    try:
        file_path = settings.output_cleaned / OUTPUT_FILE_NAME
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="cleaned_dataset.csv not found")
        return FileResponse(path=file_path, filename=file_path.name, media_type="text/csv")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
