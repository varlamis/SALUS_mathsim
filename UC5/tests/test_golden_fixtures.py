import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name,schema_name", [("event.valid.json", "event.schema.json"), ("evidence.valid.json", "evidence.schema.json")])
def test_golden_fixture_matches_schema(name, schema_name):
    fixture = json.loads((ROOT / "tests/fixtures/uc5" / name).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "models/schemas" / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(fixture)
