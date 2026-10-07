from __future__ import annotations

import copy
import json

import yaml
from jsonschema import Draft202012Validator


def _contracts(repo_root):
    return yaml.safe_load((repo_root / "contracts" / "integration" / "uc4_integration_contracts.yaml").read_text(encoding="utf-8"))


def test_all_seven_integration_contracts_validate_and_resolve(repo_root) -> None:
    document = _contracts(repo_root)
    schema = json.loads((repo_root / "models" / "schemas" / "integration_contracts.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(document)) == []
    assert {item["partner_task"] for item in document["contracts"]} == {
        "T4.4", "T4.2", "T3.3", "T3.4", "T3.5", "T3.1/T3.6", "WP6-UC4",
    }
    contract_ids = [item["contract_id"] for item in document["contracts"]]
    messages = [message for item in document["contracts"] for message in item["messages"]]
    assert len(contract_ids) == len(set(contract_ids)) == 7
    assert len({message["message_id"] for message in messages}) == len(messages) == 17
    assert all((repo_root / message["schema_ref"]).is_file() for message in messages if message["schema_ref"])


def test_integration_contract_schema_rejects_silent_required_field_change(repo_root) -> None:
    document = copy.deepcopy(_contracts(repo_root))
    document["contracts"][0]["messages"][0].pop("semantics")
    schema = json.loads((repo_root / "models" / "schemas" / "integration_contracts.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(document))
    assert any("semantics" in error.message and "required" in error.message for error in errors)
