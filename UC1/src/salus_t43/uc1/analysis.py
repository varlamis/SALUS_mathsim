from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
import random
from statistics import mean, stdev
from typing import Any
import json

import yaml

from .models import SimulationConfig
from .simulation import simulate


def interval(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "lower_95": None, "upper_95": None}
    center = mean(values)
    margin = 0.0 if len(values) == 1 else 1.96 * stdev(values) / math.sqrt(len(values))
    return {"count": len(values), "mean": center, "lower_95": center - margin, "upper_95": center + margin}


def run_analysis(root: Path, design_path: Path, sample_count: int | None = None) -> dict[str, Any]:
    design = yaml.safe_load(design_path.read_text(encoding="utf-8"))
    base = yaml.safe_load((root / design["base_config"]).read_text(encoding="utf-8"))
    count = sample_count or design["sample_count"]
    samples = []
    for offset in range(count):
        rng = random.Random(design["seed_start"] + offset)
        raw = deepcopy(base)
        raw["seed"] = design["seed_start"] + offset
        factors = {name: rng.uniform(spec["minimum"], spec["maximum"]) for name, spec in design["factors"].items()}
        raw["channel"]["loss_probability"] = factors["loss_probability"]
        raw["channel"]["observation_probability"] = factors["observation_probability"]
        raw["channel"]["jitter_seconds"] = factors["jitter_seconds"]
        raw["detection"]["threshold"] = factors["detection_threshold"]
        result = simulate(root, SimulationConfig.model_validate(raw))
        samples.append({"seed": raw["seed"], "inputs": factors, "outcomes": {key: result.documents["metrics"][key] for key in design["outcomes"]}})
    summary = {}
    for outcome in design["outcomes"]:
        values = [float(row["outcomes"][outcome]) for row in samples if row["outcomes"][outcome] is not None]
        summary[outcome] = interval(values)
    return {"schema_version": "1.0.0", "use_case": "UC1", "synthetic": True, "sample_count": count, "samples": samples, "summary": summary}


def export_analysis(result: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "monte_carlo_summary.json").write_text(json.dumps(result["summary"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "monte_carlo_samples.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in result["samples"]), encoding="utf-8")
    lines = ["# UC1 Monte Carlo report", "", f"Synthetic samples: {result['sample_count']}", "", "| Outcome | Mean | 95% interval |", "|---|---:|---:|"]
    for name, row in result["summary"].items():
        lines.append(f"| {name} | {row['mean']} | [{row['lower_95']}, {row['upper_95']}] |")
    lines.extend(["", "These are synthetic uncertainty results, not pilot performance."])
    (output / "monte_carlo_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "sensitivity.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="720" height="100"><title>UC1 declared uncertainty factors</title><text x="20" y="35">loss · observation coverage · jitter · detector threshold</text><text x="20" y="70">Synthetic design; no pilot calibration</text></svg>\n', encoding="utf-8")
