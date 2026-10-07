from __future__ import annotations

from dataclasses import replace
import json

import pytest
import yaml

from salus_t43.graph_builder import load_relationships
from salus_t43.uc4.authorization import evaluate_record
from salus_t43.uc4.migrations import migrate_simulation_config
from salus_t43.uc4.models import SimulationConfig
from salus_t43.uc4.simulation import UC4Simulation, export_result, run_simulation
from salus_t43.validation import validate_repository

from test_policy_evidence import _authorization, _record


def _raw_config(repo_root):
    return yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))


def test_config_migration_is_explicit_non_mutating_and_idempotent(repo_root) -> None:
    current = _raw_config(repo_root)
    same, no_op = migrate_simulation_config(current)
    assert same == current
    assert same is not current
    assert no_op.applied_steps == ()

    legacy = _raw_config(repo_root)
    legacy["schema_version"] = "0.9.0"
    legacy["network"].pop("background_load_fraction", None)
    legacy["collection"].pop("start_delay_seconds", None)
    migrated, report = migrate_simulation_config(legacy)
    assert legacy["schema_version"] == "0.9.0"
    assert migrated["schema_version"] == "1.0.0"
    assert migrated["network"]["background_load_fraction"] == 0.0
    assert migrated["collection"]["start_delay_seconds"] == 0.0
    assert report.source_version == "0.9.0"
    assert migrate_simulation_config(migrated)[0] == migrated
    with pytest.raises(ValueError, match="unsupported"):
        migrate_simulation_config({**current, "schema_version": "0.8.0"})


@pytest.mark.parametrize(
    ("authorization_change", "record_change", "request_time", "purpose", "reason"),
    [
        ({"decision_path": "revoked"}, {}, 920.0, None, "authorization_revoked"),
        ({}, {"subject_entity": "UC4-D99"}, 920.0, None, "entity_out_of_scope"),
        ({}, {"data_type": "payload"}, 920.0, None, "data_type_out_of_scope"),
        ({}, {"required_action": "observe_live"}, 920.0, None, "action_out_of_scope"),
        ({}, {"event_time": 800.0}, 920.0, None, "event_outside_evidence_window"),
        ({}, {}, 1600.0, None, "authorization_not_active"),
        ({}, {}, 920.0, "unrelated_secondary_use", "purpose_mismatch"),
    ],
)
def test_authorization_terms_fail_closed(
    repo_root, authorization_change, record_change, request_time, purpose, reason,
) -> None:
    authorization = _authorization(repo_root).model_copy(update=authorization_change)
    record = replace(_record(), **record_change)
    requested_purpose = purpose if purpose is not None else authorization.purpose
    decision, projection = evaluate_record(
        authorization, record, request_time, "UC4-PD-000001", requested_purpose,
    )
    assert decision.decision == "deny"
    assert decision.reason_code == reason
    assert decision.bytes_released == 0
    assert projection is None


def test_canonical_ids_vocabularies_and_twin_mapping_are_unique(repo_root) -> None:
    collection = json.loads((repo_root / "models" / "instances" / "uc4_entities.json").read_text(encoding="utf-8"))
    relationships = load_relationships(repo_root / "models" / "relationships" / "uc4_relationships.csv")
    entity_ids = [item["entity_id"] for item in collection["entities"]]
    relationship_ids = [item["relationship_id"] for item in relationships]
    assert entity_ids == [item["entity_id"] for item in json.loads(json.dumps(collection))["entities"]]
    assert len(entity_ids) == len(set(entity_ids))
    assert len(relationship_ids) == len(set(relationship_ids))

    schema = json.loads((repo_root / "models" / "schemas" / "relationship.schema.json").read_text(encoding="utf-8"))
    allowed_types = set(schema["properties"]["relationship_type"]["enum"])
    allowed_statuses = set(schema["properties"]["record_status"]["enum"])
    assert {item["relationship_type"] for item in relationships} <= allowed_types
    assert {item["record_status"] for item in relationships} <= allowed_statuses

    physical_to_twin = {item["entity_id"]: item["twin_id"] for item in collection["entities"] if item.get("twin_id")}
    twin_to_physical = {item["entity_id"]: item["physical_entity_id"] for item in collection["entities"] if item.get("physical_entity_id")}
    assert len(physical_to_twin) == len(set(physical_to_twin.values())) == 6
    assert {twin: physical for physical, twin in physical_to_twin.items()} == twin_to_physical


def test_different_random_seeds_change_stochastic_result(repo_root) -> None:
    config_path = repo_root / "configs" / "uc4" / "incident_lawful_access.yaml"
    report, _ = validate_repository(repo_root, config_path)
    raw = _raw_config(repo_root)
    first = UC4Simulation(repo_root, SimulationConfig.model_validate(raw), report).run()
    raw["random_seed"] += 1
    second = UC4Simulation(repo_root, SimulationConfig.model_validate(raw), report).run()
    assert first.canonical_result_hash != second.canonical_result_hash
    assert first.documents["observed_events"] != second.documents["observed_events"]


def test_investigator_outputs_do_not_expose_hidden_truth(repo_root, tmp_path) -> None:
    result = run_simulation(repo_root, repo_root / "configs" / "uc4" / "incident_lawful_access.yaml")
    export_result(result, tmp_path)
    hidden_marker = "presence.true_movement"
    investigator_files = {
        "observed_events.jsonl", "policy_decisions.jsonl", "evidence_manifest.json",
        "custody_events.jsonl", "reconstructed_timeline.json", "graph.json",
        "competency_queries.json", "metrics.json", "investigation_summary.md",
    }
    assert hidden_marker in (tmp_path / "ground_truth_events.jsonl").read_text(encoding="utf-8")
    assert all(hidden_marker not in (tmp_path / name).read_text(encoding="utf-8") for name in investigator_files)


def test_end_to_end_documents_are_complete_and_internally_linked(repo_root) -> None:
    result = run_simulation(repo_root, repo_root / "configs" / "uc4" / "incident_lawful_access.yaml")
    documents = result.documents
    assert {
        "entities", "relationships", "ground_truth_events", "observed_events",
        "policy_decisions", "evidence_manifest", "custody_events",
        "reconstructed_timeline", "graph", "metrics", "validation_report",
    } <= set(documents)
    assert documents["validation_report"]["status"] == "valid"
    evidence_ids = {entry["item"]["evidence_id"] for entry in documents["evidence_manifest"]["evidence"]}
    custody_evidence_ids = {entry["evidence_id"] for entry in documents["custody_events"]}
    graph_node_ids = {node["id"] for node in documents["graph"]["nodes"]}
    assert evidence_ids
    assert evidence_ids <= custody_evidence_ids
    assert evidence_ids <= graph_node_ids
    assert documents["metrics"]["integrity"]["content_and_custody_verified"] is True
    assert documents["metrics"]["privacy"]["unauthorized_disclosure_bytes"] == 0
