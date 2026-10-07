from copy import deepcopy
import json
from pathlib import Path
import random
from statistics import mean
from typing import Any
import yaml

from .experiments import _set
from .models import SimulationConfig
from .simulation import simulate


def run_analysis(root: Path, design_path: Path, samples: int | None = None) -> dict[str, Any]:
    design = yaml.safe_load(design_path.read_text(encoding="utf-8"))
    base = yaml.safe_load((root / design["base_config"]).read_text(encoding="utf-8"))
    count = samples or design["samples"]
    rng = random.Random(design["seed"])
    rows = []
    for index in range(count):
        raw = deepcopy(base)
        raw["seed"] = design["seed"] + index
        raw["scenario_id"] = f"UC5-MC-{index+1:04d}"
        sampled = {}
        for key, bounds in design["ranges"].items():
            sampled[key] = rng.uniform(bounds[0], bounds[1])
            _set(raw, key, sampled[key])
        metrics = simulate(root, SimulationConfig.model_validate(raw)).documents["metrics"]
        rows.append({"sample": index + 1, "parameters": sampled, "metrics": metrics})
    return {"schema_version": "1.0.0", "use_case": "UC5", "sample_count": count, "samples": rows, "summary": {
        "mean_alerts": mean(r["metrics"]["alert_count"] for r in rows),
        "mean_process_effects": mean(r["metrics"]["process_effect_count"] for r in rows),
        "mean_safety_rejections": mean(r["metrics"]["safety_rejection_count"] for r in rows),
        "safety_violations": sum(r["metrics"]["safety_violation_count"] for r in rows),
        "essential_monitoring_interruptions": sum(r["metrics"]["essential_monitoring_interruption_count"] for r in rows),
        "patient_data_disclosures": sum(r["metrics"]["patient_data_disclosure_count"] for r in rows),
        "privacy_violations": sum(r["metrics"]["privacy_violation_count"] for r in rows),
    }}


def export_analysis(result: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "monte_carlo_samples.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in result["samples"]), encoding="utf-8")
    summary = {k: v for k, v in result.items() if k != "samples"}
    (output / "monte_carlo_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "monte_carlo_report.md").write_text("# UC5 Monte Carlo report\n\n" + "\n".join(f"- **{k}:** {v}" for k, v in result["summary"].items()) + "\n\nSynthetic sensitivity evidence only.\n", encoding="utf-8")
    (output / "sensitivity.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="700" height="70"><text x="20" y="40">UC5 seeded sensitivity design - see JSON summary</text></svg>\n', encoding="utf-8")

