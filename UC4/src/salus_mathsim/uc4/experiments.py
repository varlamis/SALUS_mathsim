"""Resolve, execute, assert, and compare the Stage 8 UC4 experiment matrix."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import yaml

from salus_mathsim.validation import RepositoryValidationError, validate_repository

from .models import SimulationConfig
from .simulation import SimulationResult, UC4Simulation, export_result


@dataclass(frozen=True, slots=True)
class ExperimentMatrixResult:
    status: str
    rows: tuple[dict[str, Any], ...]
    failures: tuple[str, ...]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def run_experiment_matrix(
    root: Path, matrix_path: Path, output_root: Path | None = None,
) -> ExperimentMatrixResult:
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8-sig"))
    if matrix.get("schema_version") != "1.0.0":
        raise ValueError("experiment matrix schema_version must be 1.0.0")
    base_path = root / matrix["base_config"]
    base_report, _ = validate_repository(root, base_path)
    base_raw = yaml.safe_load(base_path.read_text(encoding="utf-8-sig"))
    config_schema = json.loads((root / "models" / "schemas" / "simulation_config.schema.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    seen_ids: set[str] = set()

    for definition in matrix.get("experiments", []):
        experiment_id = definition["id"]
        if experiment_id in seen_ids:
            raise ValueError(f"duplicate experiment ID: {experiment_id}")
        seen_ids.add(experiment_id)
        raw = _deep_merge(base_raw, definition.get("overrides", {}))
        raw["outputs"]["directory"] = f"reports/generated/uc4/experiments/{experiment_id}"
        schema_errors = list(Draft202012Validator(config_schema).iter_errors(raw))
        if schema_errors:
            details = "; ".join(error.message for error in schema_errors)
            raise ValueError(f"{experiment_id}: resolved configuration failed JSON Schema: {details}")
        config = SimulationConfig.model_validate(raw)
        report = {**base_report, "config": f"{matrix_path.as_posix()}#{experiment_id}"}
        result = UC4Simulation(root, config, report).run()
        if output_root is not None:
            export_result(result, output_root / experiment_id)
        row = _summarize(experiment_id, definition.get("description", ""), result)
        assertion_failures = _assert_expected(row, definition.get("expect", {}))
        row["assertions"] = {"status": "pass" if not assertion_failures else "fail", "failures": assertion_failures}
        failures.extend(f"{experiment_id}: {message}" for message in assertion_failures)
        rows.append(row)

    result = ExperimentMatrixResult("valid" if not failures else "failed", tuple(rows), tuple(failures))
    if output_root is not None:
        _write_comparison(result, output_root)
    return result


def _summarize(experiment_id: str, description: str, result: SimulationResult) -> dict[str, Any]:
    documents = result.documents
    events = documents["observed_events"]
    decisions = documents["policy_decisions"]
    evidence = documents["evidence_manifest"]["evidence"]
    metrics = documents["metrics"]
    reconstruction = documents["reconstructed_timeline"]
    return {
        "experiment_id": experiment_id,
        "description": description,
        "canonical_result_sha256": result.canonical_result_hash,
        "ground_truth_event_types": sorted({item["event_type"] for item in documents["ground_truth_events"]}),
        "observed_event_types": sorted({item["event_type"] for item in events}),
        "policy_counts": {
            decision: sum(item["decision"] == decision for item in decisions)
            for decision in ("allow", "minimize", "deny")
        },
        "evidence_items": len(evidence),
        "verified_evidence_items": sum(item["item"]["custody_status"] == "verified" for item in evidence),
        "quarantined_evidence_items": metrics["integrity"]["quarantined_evidence_items"],
        "integrity_valid": metrics["integrity"]["content_and_custody_verified"],
        "unauthorized_disclosure_bytes": metrics["privacy"]["unauthorized_disclosure_bytes"],
        "losses": metrics["network"]["loss_by_cause"],
        "queue_loss_rate": metrics["network"]["queue_loss_rate"],
        "ambiguous_ordering_links": sum(item["classification"] == "ambiguous" for item in reconstruction.get("ordering", [])),
        "maximum_uncertainty_width_seconds": max(
            (item["uncertainty_interval"]["end"] - item["uncertainty_interval"]["start"]
             for item in reconstruction.get("observations", []) if item.get("uncertainty_interval")),
            default=None,
        ),
        "claim_qualifications": {item["claim_type"]: item["qualification"] for item in reconstruction.get("claims", [])},
    }


def _assert_expected(row: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    truth = set(row["ground_truth_event_types"])
    observed = set(row["observed_event_types"])
    incident_present = {"door.open", "device.offline"}.issubset(truth)
    if expected.get("incident") == "present" and not incident_present:
        failures.append("incident ground truth is missing")
    if expected.get("incident") == "absent" and incident_present:
        failures.append("unexpected incident ground truth")
    if expected.get("evidence") == "positive" and row["evidence_items"] <= 0:
        failures.append("expected evidence but none was produced")
    if expected.get("evidence") == "zero" and row["evidence_items"] != 0:
        failures.append("expected zero evidence")
    policy = expected.get("policy")
    if policy == "allow" and row["policy_counts"]["allow"] + row["policy_counts"]["minimize"] <= 0:
        failures.append("expected an allow/minimize policy outcome")
    if policy == "deny" and row["policy_counts"]["deny"] <= 0:
        failures.append("expected a deny policy outcome")
    if policy == "none" and sum(row["policy_counts"].values()) != 0:
        failures.append("expected no acquisition policy evaluation")
    if expected.get("integrity") == "pass" and not row["integrity_valid"]:
        failures.append("expected valid content and custody")
    if expected.get("integrity") == "fail" and row["integrity_valid"]:
        failures.append("injected integrity fault was not detected")
    loss_key = expected.get("loss_key")
    if loss_key and row["losses"].get(loss_key, 0) <= 0:
        failures.append(f"expected positive {loss_key} loss count")
    absent_event = expected.get("absent_observed_event")
    if absent_event and absent_event in observed:
        failures.append(f"observed event {absent_event} should be absent")
    if expected.get("queue_loss") == "positive" and not (row["queue_loss_rate"] and row["queue_loss_rate"] > 0):
        failures.append("expected positive queue loss rate")
    if expected.get("ambiguous_ordering") == "positive" and row["ambiguous_ordering_links"] <= 0:
        failures.append("expected ambiguous ordering")
    minimum_width = expected.get("minimum_uncertainty_width_seconds")
    if minimum_width is not None and not (
        row["maximum_uncertainty_width_seconds"] is not None
        and row["maximum_uncertainty_width_seconds"] >= minimum_width
    ):
        failures.append(f"expected uncertainty width of at least {minimum_width} seconds")
    if row["unauthorized_disclosure_bytes"] != 0:
        failures.append("unauthorized disclosure must remain zero")
    return failures


def _write_comparison(result: ExperimentMatrixResult, output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    document = {"schema_version": "1.0.0", "status": result.status, "failures": list(result.failures), "experiments": list(result.rows)}
    (output_root / "experiment_comparison.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# UC4 Stage 8 experiment comparison", "", f"Overall status: **{result.status}**", "",
        "| Experiment | Evidence | Verified | Denies | Integrity | Disclosure bytes | Queue loss | Assertions |",
        "|---|---:|---:|---:|---|---:|---:|---|",
    ]
    for row in result.rows:
        lines.append(
            f"| `{row['experiment_id']}` | {row['evidence_items']} | {row['verified_evidence_items']} | "
            f"{row['policy_counts']['deny']} | {'pass' if row['integrity_valid'] else 'detected fault'} | "
            f"{row['unauthorized_disclosure_bytes']} | {row['queue_loss_rate']} | {row['assertions']['status']} |"
        )
    lines.extend(["", "All results are synthetic and do not establish legal compliance, admissibility, or real-device performance.", ""])
    (output_root / "experiment_comparison.md").write_text("\n".join(lines), encoding="utf-8")
