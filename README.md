# Autonomous Data Cleaning, Feature Engineering and Blockchain-based Data Integrity System

## Overview
This system automates dataset preparation for machine learning by chaining:
- data ingestion
- profiling
- issue detection
- AI strategy selection
- cleaning
- feature engineering
- validation
- blockchain-style audit logging

## Project Structure
- `backend/`: FastAPI API and data prep engine
- `frontend/`: React dashboard for dataset upload and reporting
- `blockchain/contracts/`: Solidity audit contract
- `tests/`: pipeline test

## Backend Setup
1. `cd backend`
2. `pip install -r requirements.txt`
3. `uvicorn main:app --reload`

API endpoints:
- `GET /api/health`
- `POST /api/process` (multipart form: `file`, optional `target_column`)

## Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

Frontend expects backend at `http://localhost:8000/api`.

## Outputs
Generated artifacts are written to:
- `backend/outputs/cleaned_data`
- `backend/outputs/reports`
- `backend/outputs/pipelines`

Audit log file:
- `backend/outputs/reports/audit_log.jsonl`
