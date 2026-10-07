"""Seeded UC4 Monte Carlo analysis and dependency-free statistical reporting."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import fmean, stdev
from typing import Any

import yaml

from salus_mathsim.validation import validate_repository

from .collection import canonical_json_bytes
from .models import SimulationConfig
from .simulation import SimulationResult, UC4Simulation, export_result


Z_95 = 1.959963984540054


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    nominal: SimulationResult
    samples: tuple[dict[str, Any], ...]
    summary: dict[str, Any]
    report_markdown: str
    sensitivity_svg: str


def mean_confidence_interval(values: list[float | None], z: float = Z_95) -> dict[str, Any]:
    usable = [float(value) for value in values if value is not None and math.isfinite(float(value))]
    undefined = len(values) - len(usable)
    if not usable:
        return {"n": 0, "undefined": undefined, "mean": None, "lower": None, "upper": None, "method": "normal_mean_95"}
    mean = fmean(usable)
    margin = z * stdev(usable) / math.sqrt(len(usable)) if len(usable) > 1 else 0.0
    return {
        "n": len(usable), "undefined": undefined, "mean": mean,
        "lower": mean - margin, "upper": mean + margin, "method": "normal_mean_95",
    }


def wilson_interval(successes: int, trials: int, z: float = Z_95) -> dict[str, Any]:
    if trials == 0:
        return {"successes": successes, "n": 0, "proportion": None, "lower": None, "upper": None, "method": "wilson_score_95"}
    proportion = successes / trials
    denominator = 1 + z * z / trials
    centre = (proportion + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / trials + z * z / (4 * trials * trials)) / denominator
    return {
        "successes": successes, "n": trials, "proportion": proportion,
        "lower": max(0.0, centre - margin), "upper": min(1.0, centre + margin), "method": "wilson_score_95",
    }


def pearson(values_x: list[float], values_y: list[float]) -> float | None:
    if len(values_x) != len(values_y) or len(values_x) < 2:
        return None
    mean_x, mean_y = fmean(values_x), fmean(values_y)
    delta_x = [value - mean_x for value in values_x]
    delta_y = [value - mean_y for value in values_y]
    denominator = math.sqrt(sum(value * value for value in delta_x) * sum(value * value for value in delta_y))
    return sum(x * y for x, y in zip(delta_x, delta_y, strict=True)) / denominator if denominator else None


def _require_design(raw: dict[str, Any]) -> None:
    required_factors = {
        "observation_loss_probability", "clock_offset_bound_seconds",
        "network_background_load_fraction", "sensor_error_probability",
        "collection_start_delay_seconds",
    }
    if raw.get("schema_version") != "1.0.0":
        raise ValueError("Monte Carlo schema_version must be 1.0.0")
    design = raw.get("design", {})
    if not isinstance(design.get("sample_count"), int) or design["sample_count"] < 2:
        raise ValueError("design.sample_count must be an integer >= 2")
    if not isinstance(design.get("master_seed"), int) or not isinstance(design.get("simulation_seed_start"), int):
        raise ValueError("design master_seed and simulation_seed_start must be integers")
    factors = raw.get("factors", {})
    if set(factors) != required_factors:
        raise ValueError(f"factors must be exactly {sorted(required_factors)}")
    for name, bounds in factors.items():
        if set(bounds) != {"distribution", "minimum", "maximum"} or bounds["distribution"] != "uniform":
            raise ValueError(f"{name} must define a uniform minimum/maximum")
        if not 0 <= float(bounds["minimum"]) <= float(bounds["maximum"]):
            raise ValueError(f"invalid bounds for {name}")


def _draw_inputs(rng: random.Random, factors: dict[str, Any]) -> dict[str, float]:
    return {
        name: rng.uniform(float(spec["minimum"]), float(spec["maximum"]))
        for name, spec in sorted(factors.items())
    }


def _sample_config(base: dict[str, Any], inputs: dict[str, float], seed: int) -> SimulationConfig:
    raw = deepcopy(base)
    raw["random_seed"] = seed
    raw["observation"]["base_loss_probability"] = inputs["observation_loss_probability"]
    bound = inputs["clock_offset_bound_seconds"]
    raw["observation"]["clock_offset_bound_seconds"] = bound
    for index, profile in enumerate(raw["devices"].values()):
        profile["clock_offset_seconds"] = bound * (0.8 if index % 2 == 0 else -0.8)
        profile["error_probability"] = inputs["sensor_error_probability"]
    raw["network"]["background_load_fraction"] = inputs["network_background_load_fraction"]
    raw["collection"]["start_delay_seconds"] = inputs["collection_start_delay_seconds"]
    raw["outputs"]["directory"] = "reports/generated/uc4/monte_carlo/not_exported"
    return SimulationConfig.model_validate(raw)


def _outcomes(metrics: dict[str, Any], reconstruction: dict[str, Any]) -> dict[str, Any]:
    strong_claims = sum(claim.get("qualification") == "strong" for claim in reconstruction.get("claims", []))
    return {
        "capture_recall": metrics["evidence"]["capture_recall"],
        "evidence_precision": metrics["evidence"]["evidence_precision"],
        "evidence_items": metrics["evidence"]["preserved_items"],
        "unauthorized_disclosure_bytes": metrics["privacy"]["unauthorized_disclosure_bytes"],
        "collection_latency_p95_seconds": metrics["collection_latency_seconds"]["p95"],
        "investigation_latency_seconds": metrics["investigation_latency_seconds"],
        "reconstruction_recall": metrics["reconstruction"]["recall"],
        "reconstruction_precision": metrics["reconstruction"]["precision"],
        "timestamp_mae_seconds": metrics["reconstruction"]["timestamp_mean_absolute_error_seconds"],
        "custody_failures": metrics["integrity"]["detected_failures"],
        "twin_mean_lag_seconds": metrics["twins"]["mean_lag_seconds"],
        "twin_stale_state_fraction": metrics["twins"]["stale_state_fraction"],
        "queue_loss_rate": metrics["network"]["queue_loss_rate"],
        "maximum_queue_occupancy_bytes": metrics["network"]["maximum_queue_occupancy_bytes"],
        "acquisition_utilization": metrics["network"]["acquisition"]["utilization"],
        "acquisition_queue_occupancy_bytes": metrics["network"]["acquisition"]["maximum_queue_occupancy_bytes"],
        "acquisition_loss_rate": metrics["network"]["acquisition"]["loss_rate"],
        "strong_claim_count": strong_claims,
    }


def _summarize(samples: list[dict[str, Any]], design: dict[str, Any]) -> dict[str, Any]:
    output_names = list(samples[0]["outcomes"])
    confidence_intervals = {
        name: mean_confidence_interval([sample["outcomes"][name] for sample in samples])
        for name in output_names
    }
    proportions = {
        "evidence_captured": wilson_interval(sum(sample["outcomes"]["evidence_items"] > 0 for sample in samples), len(samples)),
        "zero_unauthorized_disclosure": wilson_interval(sum(sample["outcomes"]["unauthorized_disclosure_bytes"] == 0 for sample in samples), len(samples)),
        "at_least_one_strong_claim": wilson_interval(sum(sample["outcomes"]["strong_claim_count"] > 0 for sample in samples), len(samples)),
        "custody_without_detected_failure": wilson_interval(sum(sample["outcomes"]["custody_failures"] == 0 for sample in samples), len(samples)),
    }
    sensitivity: dict[str, dict[str, Any]] = {}
    for factor in samples[0]["inputs"]:
        sensitivity[factor] = {}
        for output in output_names:
            paired = [
                (float(sample["inputs"][factor]), float(sample["outcomes"][output]))
                for sample in samples if sample["outcomes"][output] is not None
            ]
            coefficient = pearson([x for x, _ in paired], [y for _, y in paired]) if paired else None
            sensitivity[factor][output] = {"pearson_r": coefficient, "n": len(paired)}
    return {
        "schema_version": "1.0.0",
        "analysis_type": "synthetic_seeded_monte_carlo",
        "sample_count": len(samples),
        "master_seed": design["master_seed"],
        "simulation_seeds": [sample["simulation_seed"] for sample in samples],
        "confidence_level": 0.95,
        "confidence_interval_methods": {
            "continuous_means": "two-sided normal approximation using sample standard deviation",
            "binary_proportions": "two-sided Wilson score interval",
            "undefined_values": "excluded from continuous mean; n and undefined count reported",
        },
        "confidence_intervals": confidence_intervals,
        "proportions": proportions,
        "sensitivity_method": "Pearson product-moment correlation; descriptive, not causal",
        "sensitivity": sensitivity,
        "interpretation_boundary": "Synthetic uncalibrated model output; not measured pilot performance or proof of legal compliance.",
    }


def _fmt(value: Any) -> str:
    return "undefined" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)


def _report(summary: dict[str, Any]) -> str:
    rows = []
    for name, interval in summary["confidence_intervals"].items():
        rows.append(f"| `{name}` | {interval['n']} | {interval['undefined']} | {_fmt(interval['mean'])} | [{_fmt(interval['lower'])}, {_fmt(interval['upper'])}] |")
    ranking = []
    for factor, outputs in summary["sensitivity"].items():
        for output, entry in outputs.items():
            if entry["pearson_r"] is not None:
                ranking.append((abs(entry["pearson_r"]), factor, output, entry["pearson_r"], entry["n"]))
    ranking.sort(reverse=True)
    sensitivity_rows = [f"| `{factor}` | `{output}` | {_fmt(value)} | {n} |" for _, factor, output, value, n in ranking[:15]]
    nominal_rows = [
        f"| `{name}` | {_fmt(value)} |"
        for name, value in summary["nominal"]["outcomes"].items()
    ]
    return f"""# UC4 Stage 10 Monte Carlo analysis

This report contains synthetic, uncalibrated model results. It is not pilot performance, legal validation, or evidence of real-device fidelity.

## Reproducibility and inference

- Samples: **{summary['sample_count']}** independently parameterized, deterministically seeded runs.
- Master seed: **{summary['master_seed']}**; every simulation seed is retained in `monte_carlo_summary.json` and every row in `monte_carlo_samples.jsonl`.
- Continuous outcomes: two-sided 95% normal-approximation interval for the mean using the sample standard deviation.
- Binary outcomes: two-sided 95% Wilson score interval.
- Undefined outcomes are never coerced to zero; the table records both usable and undefined counts.
- Sensitivity is Pearson correlation and is descriptive, not causal.

## Deterministic nominal reference

Seed: **{summary['nominal']['simulation_seed']}**  
Canonical result SHA-256: `{summary['nominal']['canonical_result_sha256']}`

| Outcome | Nominal value |
|---|---:|
{chr(10).join(nominal_rows)}

## Outcome intervals

| Outcome | n | Undefined | Mean | 95% CI |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

## Largest absolute input/output correlations

| Uncertain input | Outcome | Pearson r | Paired n |
|---|---|---:|---:|
{chr(10).join(sensitivity_rows)}

## Technical boundary

Zero unauthorized disclosure in these tested paths means that no denied synthetic policy decision released bytes. It does not prove statutory compliance. Custody results verify the implemented hash-chain abstraction, not legal admissibility. Values must be recalibrated against lab or pilot measurements before operational claims are made.

## Relationship to proposal targets

The zero-disclosure, complete modeled-custody, deterministic replay, and bounded reconstruction results are technical evidence relevant to the proposal's privacy-preserving investigation, trustworthy evidence handling, Digital Twin, and reproducibility aims. They are not direct measurements of proposal KPIs and do not demonstrate performance on pilot infrastructure.
"""


def _svg(summary: dict[str, Any]) -> str:
    outputs = ["capture_recall", "reconstruction_recall", "timestamp_mae_seconds", "acquisition_utilization", "investigation_latency_seconds"]
    factors = list(summary["sensitivity"])
    cell_w, cell_h, left, top = 145, 38, 270, 100
    width, height = left + len(outputs) * cell_w + 30, top + len(factors) * cell_h + 75
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>',
             '<style>text{font-family:Arial,sans-serif;fill:#17202a}.title{font-size:18px;font-weight:bold}.label{font-size:11px}.value{font-size:12px;font-weight:bold}</style>',
             '<text x="20" y="28" class="title">UC4 synthetic sensitivity (Pearson r)</text>',
             '<text x="20" y="50" class="label">Blue: positive; orange: negative; grey: undefined. Descriptive, not causal.</text>']
    for col, output in enumerate(outputs):
        x = left + col * cell_w + cell_w / 2
        parts.append(f'<text x="{x}" y="82" text-anchor="middle" class="label">{output}</text>')
    for row, factor in enumerate(factors):
        y = top + row * cell_h
        parts.append(f'<text x="260" y="{y + 24}" text-anchor="end" class="label">{factor}</text>')
        for col, output in enumerate(outputs):
            x = left + col * cell_w
            value = summary["sensitivity"][factor][output]["pearson_r"]
            if value is None:
                color, label = "#d5d8dc", "NA"
            else:
                intensity = int(35 + 190 * abs(value))
                color = f"rgb({255-intensity//3},{255-intensity//2},{255-intensity})" if value >= 0 else f"rgb(255,{255-intensity//2},{255-intensity})"
                label = f"{value:+.2f}"
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w-4}" height="{cell_h-4}" rx="3" fill="{color}"/>')
            parts.append(f'<text x="{x + (cell_w-4)/2}" y="{y+23}" text-anchor="middle" class="value">{label}</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def run_monte_carlo(root: Path, design_path: Path, sample_count: int | None = None) -> MonteCarloResult:
    raw = yaml.safe_load(design_path.read_text(encoding="utf-8-sig"))
    _require_design(raw)
    design = dict(raw["design"])
    if sample_count is not None:
        if sample_count < 2:
            raise ValueError("sample_count override must be >= 2")
        design["sample_count"] = sample_count
    base_path = root / raw["base_config"]
    validation_report, _ = validate_repository(root, base_path)
    base = yaml.safe_load(base_path.read_text(encoding="utf-8-sig"))
    nominal_config = SimulationConfig.model_validate(base)
    nominal = UC4Simulation(root, nominal_config, validation_report).run()
    rng = random.Random(design["master_seed"])
    samples: list[dict[str, Any]] = []
    for index in range(design["sample_count"]):
        inputs = _draw_inputs(rng, raw["factors"])
        seed = design["simulation_seed_start"] + index
        config = _sample_config(base, inputs, seed)
        result = UC4Simulation(root, config, validation_report).run()
        sample = {
            "sample_index": index, "simulation_seed": seed, "inputs": inputs,
            "outcomes": _outcomes(result.documents["metrics"], result.documents["reconstructed_timeline"]),
            "canonical_result_sha256": result.canonical_result_hash,
        }
        sample["sample_sha256"] = hashlib.sha256(canonical_json_bytes(sample)).hexdigest()
        samples.append(sample)
    summary = _summarize(samples, design)
    summary["nominal"] = {
        "simulation_seed": nominal_config.random_seed,
        "canonical_result_sha256": nominal.canonical_result_hash,
        "outcomes": _outcomes(nominal.documents["metrics"], nominal.documents["reconstructed_timeline"]),
    }
    summary["samples_sha256"] = hashlib.sha256(b"\n".join(canonical_json_bytes(sample) for sample in samples)).hexdigest()
    return MonteCarloResult(nominal, tuple(samples), summary, _report(summary), _svg(summary))


def export_monte_carlo(result: MonteCarloResult, output_directory: Path) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    export_result(result.nominal, output_directory / "nominal")
    (output_directory / "monte_carlo_samples.jsonl").write_bytes(
        b"".join(canonical_json_bytes(sample) + b"\n" for sample in result.samples)
    )
    (output_directory / "monte_carlo_summary.json").write_bytes(canonical_json_bytes(result.summary) + b"\n")
    (output_directory / "monte_carlo_report.md").write_text(result.report_markdown, encoding="utf-8")
    (output_directory / "sensitivity.svg").write_text(result.sensitivity_svg, encoding="utf-8")
