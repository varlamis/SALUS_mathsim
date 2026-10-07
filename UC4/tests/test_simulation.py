import inspect
import json

from jsonschema import Draft202012Validator

from salus_t43.uc4.reconstruction import reconstruct
from salus_t43.uc4.simulation import export_result, run_simulation


def test_incident_run_is_reproducible_and_schema_valid(repo_root):
    config = repo_root / "configs" / "uc4" / "incident_lawful_access.yaml"
    first = run_simulation(repo_root, config)
    second = run_simulation(repo_root, config)
    assert first.canonical_result_hash == second.canonical_result_hash
    assert first.documents["run_manifest"]["generation_time_excluded_from_canonical_hash"] is True

    event_schema = json.loads((repo_root / "models" / "schemas" / "event.schema.json").read_text(encoding="utf-8"))
    evidence_schema = json.loads((repo_root / "models" / "schemas" / "evidence.schema.json").read_text(encoding="utf-8"))
    for event in first.documents["ground_truth_events"] + first.documents["observed_events"]:
        assert list(Draft202012Validator(event_schema).iter_errors(event)) == []
    for evidence in first.documents["evidence_manifest"]["evidence"]:
        assert list(Draft202012Validator(evidence_schema).iter_errors(evidence["item"])) == []


def test_incident_truth_policy_evidence_and_reconstruction_separation(repo_root):
    result = run_simulation(repo_root, repo_root / "configs" / "uc4" / "incident_lawful_access.yaml")
    truth_types = {event["event_type"] for event in result.documents["ground_truth_events"]}
    assert {"door.open", "device.tamper", "device.offline"}.issubset(truth_types)
    assert result.documents["evidence_manifest"]["evidence"]
    assert all(item["custody_status"] == "verified" for item in (entry["item"] for entry in result.documents["evidence_manifest"]["evidence"]))
    assert result.documents["metrics"]["privacy"]["unauthorized_disclosure_bytes"] == 0
    assert "ground_truth" not in inspect.signature(reconstruct).parameters
    evidence_ids = {entry["item"]["evidence_id"] for entry in result.documents["evidence_manifest"]["evidence"]}
    for claim in result.documents["reconstructed_timeline"]["claims"]:
        assert set(claim["evidence_ids"]).issubset(evidence_ids)


def test_baseline_has_no_incident_or_protected_collection(repo_root):
    result = run_simulation(repo_root, repo_root / "configs" / "uc4" / "baseline.yaml")
    truth_types = {event["event_type"] for event in result.documents["ground_truth_events"]}
    assert "door.open" not in truth_types
    assert "device.tamper" not in truth_types
    assert result.documents["evidence_manifest"]["evidence"] == []


def test_export_contains_every_required_run_artifact(repo_root, tmp_path):
    result = run_simulation(repo_root, repo_root / "configs" / "uc4" / "incident_lawful_access.yaml")
    export_result(result, tmp_path)
    expected = {
        "run_manifest.json", "resolved_config.yaml", "entities.json", "relationships.json",
        "ground_truth_events.jsonl", "observed_events.jsonl", "policy_decisions.jsonl",
        "evidence_manifest.json", "custody_events.jsonl", "reconstructed_timeline.json",
        "graph.json", "competency_queries.json", "graph_overview.svg", "metrics.json",
        "validation_report.json", "investigation_summary.md",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected
