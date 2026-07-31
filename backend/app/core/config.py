from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = BASE_DIR / "config.yaml"


@dataclass
class Settings:
	app_name: str
	api_prefix: str
	output_cleaned: Path
	output_reports: Path
	output_pipelines: Path
	audit_log_path: Path


def _load_yaml(path: Path) -> Dict[str, Any]:
	if not path.exists():
		return {}
	with path.open("r", encoding="utf-8") as file:
		return yaml.safe_load(file) or {}


def get_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> Settings:
	raw = _load_yaml(config_path)
	app = raw.get("app", {})
	output = raw.get("output", {})
	audit = raw.get("audit", {})

	settings = Settings(
		app_name=app.get("name", "Autonomous Data Prep System"),
		api_prefix=app.get("api_prefix", "/api"),
		output_cleaned=BASE_DIR / output.get("cleaned_data_dir", "outputs/cleaned_data"),
		output_reports=BASE_DIR / output.get("reports_dir", "outputs/reports"),
		output_pipelines=BASE_DIR / output.get("pipelines_dir", "outputs/pipelines"),
		audit_log_path=BASE_DIR / audit.get("log_file", "outputs/reports/audit_log.jsonl"),
	)

	settings.output_cleaned.mkdir(parents=True, exist_ok=True)
	settings.output_reports.mkdir(parents=True, exist_ok=True)
	settings.output_pipelines.mkdir(parents=True, exist_ok=True)
	settings.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
	return settings
