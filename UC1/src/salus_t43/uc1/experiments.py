from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml

from .models import SimulationConfig
from .simulation import SimulationResult, simulate


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def run_matrix(root: Path, matrix_path: Path) -> dict[str, Any]:
    design = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    base_path = root / design["base_config"]
    base = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    rows = []
    failures = []
    for experiment in design["experiments"]:
        raw = deep_merge(base, experiment.get("overrides", {}))
        raw["scenario_id"] = f"UC1-{experiment['id']}"
        raw["outputs"]["directory"] = f"reports/generated/uc1/experiments/{experiment['id']}"
        result = simulate(root, SimulationConfig.model_validate(raw))
        metrics = result.documents["metrics"]
        row = {"id": experiment["id"], "canonical_hash": result.canonical_hash, "alert_count": len(result.documents["alerts"]), **metrics}
        rows.append(row)
        expected = experiment.get("expect", {})
        checks = {
            "alerts": len(result.documents["alerts"]),
            "alerts_min": len(result.documents["alerts"]),
            "controller_effects": metrics["controller_effect_count"],
            "safety_violations": metrics["safety_violation_count"],
            "loss_min": sum(metrics["losses"].values()),
            "observed_attacks": metrics["attack_messages_observed"],
        }
        for key, wanted in expected.items():
            actual = checks[key]
            ok = actual >= wanted if key.endswith("_min") else actual == wanted
            if not ok:
                failures.append(f"{experiment['id']}:{key}: expected {wanted}, got {actual}")
    return {"schema_version": "1.0.0", "use_case": "UC1", "status": "pass" if not failures else "fail", "experiments": rows, "failures": failures}
