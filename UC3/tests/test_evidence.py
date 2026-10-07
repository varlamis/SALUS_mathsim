from copy import deepcopy
from salus_t43.uc3.evidence import verify
from salus_t43.uc3.simulation import run_simulation


def test_evidence_and_custody_verify(repo_root, nominal_config):
    result = run_simulation(repo_root, nominal_config)
    assert verify(result.documents["evidence_manifest"], result.documents["custody_events"]) == []


def test_content_tampering_detected(repo_root, nominal_config):
    result = run_simulation(repo_root, nominal_config)
    evidence = deepcopy(result.documents["evidence_manifest"])
    evidence[0]["content"]["event_type"] = "tampered"
    assert any("content hash mismatch" in error for error in verify(evidence, result.documents["custody_events"]))


def test_custody_tampering_detected(repo_root, nominal_config):
    result = run_simulation(repo_root, nominal_config)
    custody = deepcopy(result.documents["custody_events"])
    custody[0]["previous_hash"] = "f" * 64
    assert any("custody verification failed" in error for error in verify(result.documents["evidence_manifest"], custody))
