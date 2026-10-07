from salus_mathsim.uc3.analysis import run_analysis
from salus_mathsim.uc3.experiments import run_matrix


def test_experiment_matrix_passes(repo_root):
    result = run_matrix(repo_root, repo_root / "configs/uc3/experiments.yaml")
    assert result["status"] == "pass"
    assert len(result["experiments"]) == 9


def test_safety_rejects_fault_isolation(repo_root):
    result = run_matrix(repo_root, repo_root / "configs/uc3/experiments.yaml")
    branch = next(row for row in result["experiments"] if row["id"] == "unsafe_isolation_rejected")
    assert branch["passed"]
    assert branch["safety_violation_count"] == 0


def test_analysis_is_seeded(repo_root):
    path = repo_root / "configs/uc3/monte_carlo.yaml"
    first = run_analysis(repo_root, path, 5)
    second = run_analysis(repo_root, path, 5)
    assert first == second
    assert first["sample_count"] == 5
    assert first["summary"]["safety_violations"] == 0
