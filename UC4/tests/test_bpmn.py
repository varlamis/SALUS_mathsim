from salus_t43.validation import validate_bpmn


def test_all_bpmn_models_pass_structural_validation(repo_root):
    paths = sorted((repo_root / "diagrams").rglob("*.bpmn"))
    assert len(paths) == 7
    errors = [error for path in paths for error in validate_bpmn(path)]
    assert errors == []
