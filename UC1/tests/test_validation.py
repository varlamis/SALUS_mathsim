from copy import deepcopy
import json

import pytest
import yaml
from jsonschema import Draft202012Validator

from salus_t43.uc1.models import SimulationConfig
from salus_t43.validation import validate_repository


def test_repository_and_both_primary_configs_validate(repo_root):
    for name in ("baseline.yaml", "forged_message_attack.yaml"):
        report = validate_repository(repo_root, repo_root / "configs/uc1" / name)
        assert report == {"status": "valid", "entities": 30, "relationships": 60, "schemas": 9, "bpmn": 7}


def test_config_rejects_unknown_and_escaping_output(repo_root):
    raw = yaml.safe_load((repo_root / "configs/uc1/forged_message_attack.yaml").read_text())
    bad = deepcopy(raw)
    bad["unknown"] = True
    with pytest.raises(ValueError):
        SimulationConfig.model_validate(bad)
    bad = deepcopy(raw)
    bad["outputs"]["directory"] = "../escape"
    with pytest.raises(ValueError):
        SimulationConfig.model_validate(bad)


def test_entity_instances_validate(repo_root):
    schema = json.loads((repo_root / "models/schemas/entity.schema.json").read_text())
    collection = json.loads((repo_root / "models/instances/uc1_entities.json").read_text())
    assert all(not list(Draft202012Validator(schema).iter_errors(entity)) for entity in collection["entities"])
