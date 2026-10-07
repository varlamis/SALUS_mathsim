from __future__ import annotations

import csv
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any

import networkx as nx
import yaml
from jsonschema import Draft202012Validator, RefResolver

from .uc1.graph import load_entities, load_relationships, static_graph
from .uc1.models import SimulationConfig


class RepositoryValidationError(ValueError):
    pass


def validate_repository(root: Path, config_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    schemas = root / "models/schemas"
    for path in sorted(schemas.glob("*.schema.json")):
        try:
            Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            errors.append(f"{path}: {exc}")
    config_raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        SimulationConfig.model_validate(config_raw)
    except Exception as exc:
        errors.append(f"config: {exc}")
    config_schema = json.loads((schemas / "simulation_config.schema.json").read_text(encoding="utf-8"))
    errors.extend(f"config schema: {error.message}" for error in Draft202012Validator(config_schema).iter_errors(config_raw))
    collection = load_entities(root)
    entity_schema = json.loads((schemas / "entity.schema.json").read_text(encoding="utf-8"))
    ids: set[str] = set()
    twins: dict[str, str] = {}
    for entity in collection["entities"]:
        errors.extend(f"{entity.get('entity_id')}: {error.message}" for error in Draft202012Validator(entity_schema).iter_errors(entity))
        if entity["entity_id"] in ids:
            errors.append(f"duplicate entity {entity['entity_id']}")
        ids.add(entity["entity_id"])
        if entity.get("twin_id"):
            twins[entity["entity_id"]] = entity["twin_id"]
    relationship_schema = json.loads((schemas / "relationship.schema.json").read_text(encoding="utf-8"))
    relationships = load_relationships(root)
    relation_ids: set[str] = set()
    for relation in relationships:
        errors.extend(f"{relation.get('relationship_id')}: {error.message}" for error in Draft202012Validator(relationship_schema).iter_errors(relation))
        if relation["relationship_id"] in relation_ids:
            errors.append(f"duplicate relationship {relation['relationship_id']}")
        relation_ids.add(relation["relationship_id"])
        for endpoint in (relation["source_entity"], relation["target_entity"]):
            if endpoint not in ids:
                errors.append(f"unresolved endpoint {endpoint}")
    graph = static_graph(root)
    if not nx.is_connected(graph.to_undirected()):
        errors.append("static graph is not weakly connected")
    for device, twin in twins.items():
        if twin not in ids:
            errors.append(f"missing twin {twin}")
        if not any(data.get("relationship_type") == "MIRRORED_BY" for data in graph.get_edge_data(device, twin, default={}).values()):
            errors.append(f"missing MIRRORED_BY {device}->{twin}")
    for path in sorted((root / "diagrams").rglob("*.bpmn")):
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"{path}: {exc}")
    if errors:
        raise RepositoryValidationError("UC1 validation failed:\n- " + "\n- ".join(errors))
    return {"status": "valid", "entities": len(ids), "relationships": len(relation_ids), "schemas": len(list(schemas.glob('*.schema.json'))), "bpmn": len(list((root / 'diagrams').rglob('*.bpmn')))}
