import json

import pytest
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from salus_t43.uc4.models import EvidenceItem, SimulationConfig, UC4Event
from salus_t43.validation import validate_repository


@pytest.mark.parametrize("config_name", ["baseline.yaml", "incident_lawful_access.yaml"])
def test_repository_contracts_validate(repo_root, config_name):
    report, _document = validate_repository(repo_root, repo_root / "configs" / "uc4" / config_name)
    assert report["status"] == "valid"
    assert report["entities"] == 38
    assert report["relationships"] == 123


def test_valid_event_and_evidence_round_trip(repo_root):
    fixtures = repo_root / "tests" / "fixtures" / "uc4"
    event_raw = json.loads((fixtures / "event.valid.json").read_text(encoding="utf-8"))
    evidence_raw = json.loads((fixtures / "evidence.valid.json").read_text(encoding="utf-8"))
    assert json.loads(UC4Event.model_validate(event_raw).model_dump_json(exclude_none=True)) == event_raw
    assert json.loads(EvidenceItem.model_validate(evidence_raw).model_dump_json(exclude_none=True)) == evidence_raw


def test_config_rejects_unknown_key_and_bad_time(repo_root):
    raw = yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))
    raw["unexpected"] = True
    with pytest.raises(ValidationError) as exc:
        SimulationConfig.model_validate(raw)
    assert "unexpected" in str(exc.value)

    raw.pop("unexpected")
    raw["time"]["tamper"] = raw["time"]["entry"]
    with pytest.raises(ValidationError) as exc:
        SimulationConfig.model_validate(raw)
    assert "times must satisfy" in str(exc.value)


def test_config_json_schema_rejects_payload_capture(repo_root):
    raw = yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))
    raw["network"]["payload_capture_enabled"] = True
    schema = json.loads((repo_root / "models" / "schemas" / "simulation_config.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(raw))
    assert any(list(error.absolute_path)[-1] == "payload_capture_enabled" for error in errors)


def test_runtime_config_rejects_cross_field_incompatibility(repo_root):
    raw = yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))
    raw["authorization"]["verification_result"] = "unknown"
    with pytest.raises(ValidationError) as exc:
        SimulationConfig.model_validate(raw)
    assert "allow decision_path requires verification_result=valid" in str(exc.value)


def test_runtime_config_rejects_unknown_device_profile(repo_root):
    raw = yaml.safe_load((repo_root / "configs" / "uc4" / "incident_lawful_access.yaml").read_text(encoding="utf-8"))
    raw["devices"]["UC4-D99"] = raw["devices"].pop("UC4-D06")
    with pytest.raises(ValidationError) as exc:
        SimulationConfig.model_validate(raw)
    assert "invalid device profile key" in str(exc.value)
