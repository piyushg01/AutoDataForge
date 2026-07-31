from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline


def _generate_pipeline_code(steps: list[tuple[str, Any]]) -> str:
	imports = [
		"from sklearn.pipeline import Pipeline",
	]
	lines = ["pipeline = Pipeline(steps=["]
	for name, transformer in steps:
		transformer_name = transformer.__class__.__name__ if hasattr(transformer, "__class__") else str(transformer)
		lines.append(f"    ('{name}', {transformer_name}()),")
	lines.append("])\n")
	return "\n".join(imports + [""] + lines)


def build_and_save_pipeline(steps: list[tuple[str, object]], output_path: Path) -> dict[str, str]:
	pipeline = Pipeline(steps=steps)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	joblib.dump(pipeline, output_path)

	code_output = output_path.with_suffix(".py")
	code_output.write_text(_generate_pipeline_code(steps), encoding="utf-8")

	return {
		"pipeline_joblib_path": str(output_path),
		"pipeline_code_path": str(code_output),
	}
