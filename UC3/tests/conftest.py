from pathlib import Path
import pytest


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def nominal_config(repo_root: Path) -> Path:
    return repo_root / "configs/uc3/smart_fuzzing_attack.yaml"
