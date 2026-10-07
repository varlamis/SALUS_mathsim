import json
import xml.etree.ElementTree as ET

import yaml
from jsonschema import Draft202012Validator


def test_all_integration_contracts_validate(repo_root):
    document = yaml.safe_load((repo_root / "contracts/integration/uc1_integration_contracts.yaml").read_text())
    schema = json.loads((repo_root / "models/schemas/integration_contracts.schema.json").read_text())
    assert list(Draft202012Validator(schema).iter_errors(document)) == []
    assert len(document["contracts"]) == 8
    assert len({row["contract_id"] for row in document["contracts"]}) == 8


def test_bpmn_sequence_references_resolve(repo_root):
    namespace = {"b": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
    paths = sorted((repo_root / "diagrams").rglob("*.bpmn"))
    assert len(paths) == 7
    for path in paths:
        root = ET.parse(path).getroot()
        ids = {node.get("id") for node in root.iter() if node.get("id")}
        flows = root.findall(".//b:sequenceFlow", namespace)
        assert flows
        assert all(flow.get("sourceRef") in ids and flow.get("targetRef") in ids for flow in flows)

