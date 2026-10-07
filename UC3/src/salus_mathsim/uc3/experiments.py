from copy import deepcopy
from pathlib import Path
from typing import Any
import yaml

from .models import SimulationConfig
from .simulation import simulate


def _set(document: dict[str, Any], path: str, value: Any) -> None:
    target = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value


def run_matrix(root: Path, matrix_path: Path) -> dict[str, Any]:
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))
    base = yaml.safe_load((root / matrix["base_config"]).read_text(encoding="utf-8"))
    rows = []
    all_pass = True
    for branch in matrix["experiments"]:
        raw = deepcopy(base)
        raw["scenario_id"] = "UC3-" + branch["id"].upper().replace("_", "-")
        for key, value in branch.get("overrides", {}).items():
            _set(raw, key, value)
        result = simulate(root, SimulationConfig.model_validate(raw))
        metrics = result.documents["metrics"]
        expect = branch["expect"]
        checks = {
            "minimum_alerts": metrics["alert_count"] >= expect.get("minimum_alerts", 0),
            "maximum_process_effects": metrics["process_effect_count"] <= expect.get("maximum_process_effects", 10**9),
            "maximum_safety_violations": metrics["safety_violation_count"] <= expect.get("maximum_safety_violations", 10**9),
        }
        passed = all(checks.values())
        all_pass &= passed
        rows.append({"id": branch["id"], "passed": passed, "checks": checks, "canonical_hash": result.canonical_hash, **{k: metrics[k] for k in ("alert_count", "process_effect_count", "safety_violation_count")}})
    return {"schema_version": "1.0.0", "use_case": "UC3", "status": "pass" if all_pass else "fail", "experiments": rows}
