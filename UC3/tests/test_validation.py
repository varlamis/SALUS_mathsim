import copy
import yaml
import pytest
from salus_t43.uc3.models import SimulationConfig
from salus_t43.validation import validate_repository


def test_repository_is_complete(repo_root, nominal_config):
    assert validate_repository(repo_root, nominal_config) == {"status": "valid", "entities": 36, "relationships": 60, "schemas": 9, "bpmn": 8}


def test_unknown_config_field_rejected(nominal_config):
    raw = yaml.safe_load(nominal_config.read_text(encoding="utf-8"))
    raw["live_endpoint"] = "forbidden"
    with pytest.raises(Exception):
        SimulationConfig.model_validate(raw)


def test_invalid_process_bounds_rejected(nominal_config):
    raw = yaml.safe_load(nominal_config.read_text(encoding="utf-8"))
    raw["process"]["target_level_m"] = 99
    with pytest.raises(Exception):
        SimulationConfig.model_validate(raw)


def test_output_escape_rejected(nominal_config):
    raw = yaml.safe_load(nominal_config.read_text(encoding="utf-8"))
    raw["outputs"]["directory"] = "../outside"
    with pytest.raises(Exception):
        SimulationConfig.model_validate(raw)
