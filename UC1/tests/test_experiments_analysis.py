from salus_t43.uc1.analysis import run_analysis
from salus_t43.uc1.experiments import run_matrix


def test_declared_experiment_matrix_passes(repo_root):
    result = run_matrix(repo_root, repo_root / "configs/uc1/experiments.yaml")
    assert result["status"] == "pass"
    assert result["failures"] == []
    assert len(result["experiments"]) == 9


def test_seeded_analysis_is_reproducible(repo_root):
    path = repo_root / "configs/uc1/monte_carlo.yaml"
    first = run_analysis(repo_root, path, sample_count=10)
    second = run_analysis(repo_root, path, sample_count=10)
    assert first == second
    assert first["sample_count"] == 10
    assert first["synthetic"] is True

