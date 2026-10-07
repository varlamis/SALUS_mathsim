from salus_t43.uc4.experiments import run_experiment_matrix


def test_stage8_experiment_matrix_passes_all_declared_expectations(repo_root):
    result = run_experiment_matrix(repo_root, repo_root / "configs" / "uc4" / "experiments.yaml")
    assert result.status == "valid"
    assert result.failures == ()
    assert len(result.rows) == 16
    assert all(row["assertions"]["status"] == "pass" for row in result.rows)
    assert all(row["unauthorized_disclosure_bytes"] == 0 for row in result.rows)


def test_stage8_negative_paths_have_expected_effects(repo_root):
    result = run_experiment_matrix(repo_root, repo_root / "configs" / "uc4" / "experiments.yaml")
    rows = {row["experiment_id"]: row for row in result.rows}
    for name in (
        "authorization_absent", "authorization_invalid", "authorization_expired",
        "authorization_revoked", "out_of_scope_device",
    ):
        assert rows[name]["evidence_items"] == 0
        assert rows[name]["policy_counts"]["deny"] > 0
    assert rows["door_event_lost"]["claim_qualifications"]["automation"] == "unsupported"
    assert rows["source_records_evicted"]["evidence_items"] == 0
    assert rows["cpe_queue_overflow"]["queue_loss_rate"] > 0
    assert rows["maximum_clock_skew"]["maximum_uncertainty_width_seconds"] >= 60
    assert rows["evidence_content_tampered"]["quarantined_evidence_items"] == 1
    assert rows["custody_link_tampered"]["verified_evidence_items"] == 0
