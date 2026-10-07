from dataclasses import replace

import pytest
import yaml

from salus_t43.uc4.authorization import SourceRecord, evaluate_record
from salus_t43.uc4.collection import canonical_json_bytes, collect_evidence
from salus_t43.uc4.custody import CustodyChain
from salus_t43.uc4.models import SimulationConfig


def _authorization(repo_root):
    raw = yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))
    return SimulationConfig.model_validate(raw).authorization


def _record(event_time=600.0, subject="UC4-D03"):
    return SourceRecord(
        "UC4-SRC-000001", "UC4-D03", subject, "device_state_event", "export_state", event_time,
        {"record_id": "UC4-SRC-000001", "entity_id": subject, "event_type": "door.open", "event_time": event_time,
         "ingest_time": 601.0, "state": "open_online", "source": "UC4-D03", "correlation_ids": ["C1"],
         "quality": "estimated", "secret": "must-not-release"},
    )


def test_policy_minimizes_to_permitted_fields(repo_root):
    authorization = _authorization(repo_root)
    decision, projection = evaluate_record(authorization, _record(), 920.0, "UC4-PD-000001", authorization.purpose)
    assert decision.decision == "minimize"
    assert projection is not None
    assert "secret" not in projection
    assert set(projection).issubset(set(_authorization(repo_root).permitted_fields))


def test_policy_denies_out_of_scope_with_zero_disclosure(repo_root):
    authorization = _authorization(repo_root)
    decision, projection = evaluate_record(authorization, _record(subject="UC4-D99"), 920.0, "UC4-PD-000001", authorization.purpose)
    assert decision.decision == "deny"
    assert decision.bytes_released == 0
    assert projection is None


def test_evidence_hash_and_custody_detect_corruption(repo_root):
    record = _record()
    authorization = _authorization(repo_root)
    decision, projection = evaluate_record(authorization, record, 920.0, "UC4-PD-000001", authorization.purpose)
    evidence = collect_evidence("UC4-EV-000001", record, projection, decision, 920.1)
    assert evidence.verify_content()
    corrupted_content = {**evidence.content, "state": "closed_online"}
    assert canonical_json_bytes(corrupted_content) != canonical_json_bytes(evidence.content)

    chain = CustodyChain("UC4-RUN-1", "UC4-CASE-0001", "1.0.0")
    record_one = chain.append("UC4-CUST-000001", evidence.item.evidence_id, evidence.item.content_hash, "registered", 920.1, "UC4-S03")
    chain.append("UC4-CUST-000002", evidence.item.evidence_id, evidence.item.content_hash, "verified", 920.2, "UC4-S04")
    assert chain.verify()
    damaged = [replace(record_one, action="altered"), chain.records[1]]
    assert not chain.verify(damaged)


def test_rfc8785_canonical_number_and_key_forms():
    assert canonical_json_bytes({"z": 1.0, "a": -0.0, "small": 1e-7, "plain": 1e-6, "large": 1e21}) == (
        b'{"a":0,"large":1e+21,"plain":0.000001,"small":1e-7,"z":1}'
    )
    with pytest.raises(ValueError):
        canonical_json_bytes({"invalid": float("nan")})
