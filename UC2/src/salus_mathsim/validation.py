import csv
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import yaml
from jsonschema import Draft202012Validator, RefResolver

from .uc2.models import SimulationConfig


class RepositoryValidationError(ValueError):
    pass


def validate_repository(root: Path, config_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    schemas = sorted((root / "models/schemas").glob("*.schema.json"))
    entities_doc = json.loads((root / "models/instances/uc2_entities.json").read_text(encoding="utf-8"))
    entity_schema = json.loads((root / "models/schemas/entity_collection.schema.json").read_text(encoding="utf-8"))
    store = {json.loads(p.read_text(encoding="utf-8")).get("$id", p.name): json.loads(p.read_text(encoding="utf-8")) for p in schemas}
    resolver = RefResolver.from_schema(entity_schema, store=store)
    for error in Draft202012Validator(entity_schema, resolver=resolver).iter_errors(entities_doc):
        errors.append(f"entities: {error.message}")
    ids = [e["entity_id"] for e in entities_doc["entities"]]
    if len(ids) != len(set(ids)):
        errors.append("duplicate entity IDs")
    with (root / "models/relationships/uc2_relationships.csv").open(encoding="utf-8", newline="") as handle:
        relationships = list(csv.DictReader(handle))
    entity_ids = set(ids)
    rel_ids = [r["relationship_id"] for r in relationships]
    if len(rel_ids) != len(set(rel_ids)):
        errors.append("duplicate relationship IDs")
    for row in relationships:
        if row["source_id"] not in entity_ids or row["target_id"] not in entity_ids:
            errors.append(f"dangling relationship {row['relationship_id']}")
    try:
        SimulationConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    except Exception as exc:
        errors.append(f"config: {exc}")
    bpmn = sorted((root / "diagrams").rglob("*.bpmn"))
    for path in bpmn:
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"BPMN {path.name}: {exc}")
    contract_path = root / "contracts/integration/uc2_integration_contracts.yaml"
    if contract_path.exists():
        contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
        contract_schema = json.loads((root / "models/schemas/integration_contracts.schema.json").read_text(encoding="utf-8"))
        for error in Draft202012Validator(contract_schema).iter_errors(contract):
            errors.append(f"contracts: {error.message}")
    if errors:
        raise RepositoryValidationError("\n".join(errors))
    return {"status": "valid", "entities": len(ids), "relationships": len(relationships), "schemas": len(schemas), "bpmn": len(bpmn)}

