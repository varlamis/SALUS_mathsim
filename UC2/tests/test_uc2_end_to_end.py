from copy import deepcopy
import json
from pathlib import Path

import yaml

from salus_mathsim.handoff import build_manifest, verify_manifest
from salus_mathsim.uc2.evidence import verify
from salus_mathsim.uc2.experiments import run_matrix
from salus_mathsim.uc2.models import SimulationConfig
from salus_mathsim.uc2.simulation import simulate
from salus_mathsim.validation import validate_repository

ROOT = Path(__file__).resolve().parents[1]


def config(name="unapproved_device.yaml"):
    return SimulationConfig.model_validate(yaml.safe_load((ROOT / "configs/uc2" / name).read_text()))


def test_repository_contracts_and_bpmn_validate():
    report = validate_repository(ROOT, ROOT / "configs/uc2/unapproved_device.yaml")
    assert report == {"status": "valid", "entities": 25, "relationships": 26, "schemas": 9, "bpmn": 7}


def test_nominal_is_passive_private_and_explainable():
    result = simulate(ROOT, config()).documents
    assert result["metrics"]["alert_count"] == 1
    assert result["metrics"]["active_rf_action_count"] == 0
    assert result["metrics"]["unauthorized_disclosure_count"] == 0
    assert result["alerts"][0]["attributes"]["explanation"]
    assert all(not row["attributes"].get("payload_captured", False) for row in result["observed_events"])


def test_equal_seed_is_deterministic():
    assert simulate(ROOT, config()).canonical_hash == simulate(ROOT, config()).canonical_hash


def test_complete_loss_produces_no_alert():
    raw = config().model_dump()
    raw["observation"]["coverage_probability"] = 0.0
    assert simulate(ROOT, SimulationConfig.model_validate(raw)).documents["metrics"]["alert_count"] == 0


def test_queue_overflow_is_explicit():
    raw = config().model_dump()
    raw["observation"]["queue_capacity"] = 2
    assert simulate(ROOT, SimulationConfig.model_validate(raw)).documents["metrics"]["queue_overflow"] > 0


def test_evidence_and_custody_verify():
    documents = simulate(ROOT, config()).documents
    assert verify(documents["evidence_manifest"], documents["custody_events"]) == []


def test_reconstruction_does_not_use_hidden_truth():
    assert simulate(ROOT, config()).documents["reconstructed_timeline"]["hidden_truth_used"] is False


def test_experiment_matrix_passes():
    assert run_matrix(ROOT, ROOT / "configs/uc2/experiments.yaml")["status"] == "pass"


def test_manifest_detects_change(tmp_path):
    output = tmp_path / "manifest.json"
    manifest = build_manifest(ROOT, output)
    assert verify_manifest(ROOT, manifest) == []
    changed = deepcopy(manifest)
    changed["artifacts"][0]["sha256"] = "0" * 64
    assert verify_manifest(ROOT, changed)
