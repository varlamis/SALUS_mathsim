from salus_t43.uc3.simulation import export_result, run_simulation


def test_nominal_is_deterministic_safe_and_truth_isolated(repo_root, nominal_config):
    first = run_simulation(repo_root, nominal_config)
    second = run_simulation(repo_root, nominal_config)
    assert first.canonical_hash == second.canonical_hash
    metrics = first.documents["metrics"]
    assert metrics["alert_count"] >= 1
    assert metrics["process_effect_count"] == 0
    assert metrics["safety_violation_count"] == 0
    assert first.documents["reconstructed_timeline"]["hidden_truth_used"] is False
    assert first.documents["validation_report"]["invariants"]["live_control"] is False


def test_process_remains_bounded(repo_root, nominal_config):
    result = run_simulation(repo_root, nominal_config)
    levels = [row["level_m"] for row in result.documents["process_state"]]
    assert min(levels) >= 2.0
    assert max(levels) <= 8.0


def test_export_complete_bundle(repo_root, nominal_config, tmp_path):
    result = run_simulation(repo_root, nominal_config)
    export_result(result, tmp_path)
    required = {"run_manifest.json", "resolved_config.yaml", "entities.json", "relationships.json", "ground_truth_events.jsonl", "process_state.jsonl", "observed_events.jsonl", "protocol_validation.jsonl", "alerts.jsonl", "policy_decisions.jsonl", "mitigation_actions.jsonl", "evidence_manifest.json", "custody_events.jsonl", "reconstructed_timeline.json", "graph.json", "competency_queries.json", "metrics.json", "validation_report.json", "investigation_summary.md", "process_overview.svg", "graph_overview.svg"}
    assert required == {p.name for p in tmp_path.iterdir()}
