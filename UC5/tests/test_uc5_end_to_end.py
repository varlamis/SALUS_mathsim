from copy import deepcopy
import json
from pathlib import Path

import yaml

from salus_mathsim.handoff import build_manifest, verify_manifest
from salus_mathsim.uc5.evidence import verify
from salus_mathsim.uc5.experiments import run_matrix
from salus_mathsim.uc5.models import SimulationConfig
from salus_mathsim.uc5.simulation import simulate
from salus_mathsim.validation import validate_repository

ROOT = Path(__file__).resolve().parents[1]


def config(name="compromised_monitor.yaml"):
    raw = yaml.safe_load((ROOT / "configs/uc5" / name).read_text(encoding="utf-8"))
    return SimulationConfig.model_validate(raw)


def changed(**overrides):
    raw = config().model_dump()
    for dotted, value in overrides.items():
        target = raw
        parts = dotted.split(".")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = value
    return SimulationConfig.model_validate(raw)


def test_repository_contracts_and_bpmn_validate():
    report = validate_repository(ROOT, ROOT / "configs/uc5/compromised_monitor.yaml")
    assert report == {"status": "valid", "entities": 34, "relationships": 45, "schemas": 9, "bpmn": 8}


def test_nominal_alert_is_explainable_and_isolation_is_rejected_safely():
    documents = simulate(ROOT, config()).documents
    assert documents["metrics"]["alert_count"] == 1
    assert documents["metrics"]["safety_rejection_count"] == 1
    assert documents["metrics"]["essential_monitoring_interruption_count"] == 0
    assert documents["mitigation_actions"][0]["attributes"]["action"] == "none"
    assert documents["alerts"][0]["attributes"]["contributions"]


def test_approved_backup_permits_bounded_isolation():
    documents = simulate(ROOT, changed(**{"device.backup_monitoring": True})).documents
    assert documents["safety_decisions"][0]["attributes"]["allowed"] is True
    assert documents["mitigation_actions"][0]["attributes"]["action"] == "isolate"
    assert documents["metrics"]["essential_monitoring_interruption_count"] == 0


def test_shared_package_is_minimized_and_contains_no_patient_data():
    package = simulate(ROOT, config()).documents["shared_evidence_package"]
    assert package["status"] == "shared" and package["redacted"] is True
    assert package["patient_identifiers"] == [] and package["clinical_payloads"] == []
    serialized = json.dumps(package).lower()
    assert "patient_name" not in serialized and "diagnosis" not in serialized


def test_unauthorized_sharing_fails_closed():
    package = simulate(ROOT, changed(**{"evidence.sharing_authorized": False})).documents["shared_evidence_package"]
    assert package["status"] == "denied" and package["evidence_ids"] == []


def test_complete_observation_loss_produces_no_alert():
    documents = simulate(ROOT, changed(**{"channel.observation_probability": 0.0})).documents
    assert documents["metrics"]["alert_count"] == 0
    assert documents["metrics"]["observation_loss"] > 0


def test_health_fault_is_not_mislabeled_as_cyberattack():
    documents = simulate(ROOT, changed(**{"attack.kind": "health_fault"})).documents
    assert documents["metrics"]["alert_count"] == 0


def test_equal_seed_is_deterministic_and_evidence_verifies():
    first = simulate(ROOT, config())
    second = simulate(ROOT, config())
    assert first.canonical_hash == second.canonical_hash
    assert verify(first.documents["evidence_manifest"], first.documents["custody_events"]) == []


def test_reconstruction_and_observations_do_not_use_hidden_truth():
    documents = simulate(ROOT, config()).documents
    assert documents["reconstructed_timeline"]["hidden_truth_used"] is False
    assert all("attack_truth" not in event.get("attributes", {}) for event in documents["observed_events"])


def test_experiment_matrix_passes():
    comparison = run_matrix(ROOT, ROOT / "configs/uc5/experiments.yaml")
    assert comparison["status"] == "pass"
    assert all(row["metrics"]["essential_monitoring_interruption_count"] == 0 for row in comparison["experiments"])
    assert all(row["metrics"]["patient_data_disclosure_count"] == 0 for row in comparison["experiments"])


def test_manifest_detects_change(tmp_path):
    output = tmp_path / "manifest.json"
    manifest = build_manifest(ROOT, output)
    assert verify_manifest(ROOT, manifest) == []
    changed_manifest = deepcopy(manifest)
    changed_manifest["artifacts"][0]["sha256"] = "0" * 64
    assert verify_manifest(ROOT, changed_manifest)
