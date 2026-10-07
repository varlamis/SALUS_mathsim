from salus_mathsim.uc1.simulation import export_result, run_simulation


def test_nominal_attack_is_deterministic_safe_and_explained(repo_root):
    path = repo_root / "configs/uc1/forged_message_attack.yaml"
    first = run_simulation(repo_root, path)
    second = run_simulation(repo_root, path)
    assert first.canonical_hash == second.canonical_hash
    assert first.documents["alerts"]
    assert all(alert["attributes"]["explanation"] for alert in first.documents["alerts"])
    assert first.documents["metrics"]["controller_effect_count"] == 0
    assert first.documents["metrics"]["safety_violation_count"] == 0
    assert first.documents["metrics"]["unauthorized_disclosure_count"] == 0


def test_baseline_has_no_attack_or_alert(repo_root):
    result = run_simulation(repo_root, repo_root / "configs/uc1/baseline.yaml")
    assert result.documents["metrics"]["attack_messages_generated"] == 0
    assert result.documents["alerts"] == []


def test_hidden_truth_is_not_used_by_investigator_outputs(repo_root):
    result = run_simulation(repo_root, repo_root / "configs/uc1/forged_message_attack.yaml")
    assert result.documents["reconstructed_timeline"]["hidden_truth_used"] is False
    for name in ("graph", "competency_queries", "investigation_summary", "evidence_manifest"):
        assert "ground_truth_events" not in str(result.documents[name])


def test_export_has_complete_bundle(repo_root, tmp_path):
    result = run_simulation(repo_root, repo_root / "configs/uc1/forged_message_attack.yaml")
    export_result(result, tmp_path)
    expected = {"run_manifest.json", "resolved_config.yaml", "entities.json", "relationships.json", "ground_truth_events.jsonl", "observed_events.jsonl", "message_validation.jsonl", "alerts.jsonl", "policy_decisions.jsonl", "controller_decisions.jsonl", "evidence_manifest.json", "custody_events.jsonl", "reconstructed_timeline.json", "graph.json", "competency_queries.json", "metrics.json", "validation_report.json", "investigation_summary.md", "graph_overview.svg"}
    assert expected == {path.name for path in tmp_path.iterdir()}

