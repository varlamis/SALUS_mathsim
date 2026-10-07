from copy import deepcopy

from salus_t43.uc1.evidence import verify
from salus_t43.uc1.simulation import run_simulation


def test_evidence_is_minimized_and_custody_verifies(repo_root):
    result = run_simulation(repo_root, repo_root / "configs/uc1/forged_message_attack.yaml")
    allowed = set(result.documents["resolved_config"]["evidence"]["allowed_fields"])
    assert all(set(item["fields"]) <= allowed for item in result.documents["evidence_manifest"])
    assert verify(result.documents["evidence_manifest"], result.documents["custody_events"]) == []


def test_content_and_custody_tampering_are_detected(repo_root):
    result = run_simulation(repo_root, repo_root / "configs/uc1/forged_message_attack.yaml")
    evidence = deepcopy(result.documents["evidence_manifest"])
    custody = deepcopy(result.documents["custody_events"])
    evidence[0]["fields"]["event_type"] = "tampered"
    assert any("content hash mismatch" in error for error in verify(evidence, custody))
    evidence = deepcopy(result.documents["evidence_manifest"])
    custody[0]["action"] = "tampered"
    assert any("custody chain mismatch" in error for error in verify(evidence, custody))

