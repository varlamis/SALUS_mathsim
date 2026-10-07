"""Repository-wide pre-simulation validation for UC4."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import networkx as nx
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError as PydanticValidationError
from referencing import Registry, Resource

from .graph_builder import build_graph, graph_document, load_relationships
from .uc4.models import SCHEMA_VERSION, Entity, EvidenceItem, SimulationConfig, UC4Event

BPMN = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI = "http://www.omg.org/spec/BPMN/20100524/DI"


class RepositoryValidationError(ValueError):
    """Raised with all actionable validation failures, not only the first one."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("UC4 validation failed:\n- " + "\n- ".join(errors))


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def _json_errors(instance: Any, schema: dict[str, Any], label: str, registry: Registry | None = None) -> list[str]:
    validator = Draft202012Validator(schema, registry=registry or Registry())
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        errors.append(f"{label}:{location}: {error.message}")
    return errors


def validate_bpmn(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: XML parse error: {exc}"]
    elements = list(root.iter())
    ids = [element.get("id") for element in elements if element.get("id")]
    id_set = set(ids)
    if len(ids) != len(id_set):
        errors.append(f"{path}: duplicate BPMN IDs")
    for element in elements:
        for attribute in ("processRef", "sourceRef", "targetRef", "messageRef", "signalRef", "attachedToRef", "dataStoreRef", "dataObjectRef", "bpmnElement", "default"):
            value = element.get(attribute)
            if value and value not in id_set:
                errors.append(f"{path}: unresolved {attribute}={value}")
    processes = root.findall(f"{{{BPMN}}}process")
    owner: dict[str, str] = {}
    for process in processes:
        for element in process.iter():
            if element.get("id"):
                owner[element.get("id")] = process.get("id", "")
    sequence_flows = root.findall(f".//{{{BPMN}}}sequenceFlow")
    message_flows = root.findall(f".//{{{BPMN}}}messageFlow")
    for flow in sequence_flows:
        if owner.get(flow.get("sourceRef", "")) != owner.get(flow.get("targetRef", "")):
            errors.append(f"{path}: sequence flow {flow.get('id')} crosses a process boundary")
    for flow in message_flows:
        if owner.get(flow.get("sourceRef", "")) == owner.get(flow.get("targetRef", "")):
            errors.append(f"{path}: message flow {flow.get('id')} does not cross a process boundary")
    outgoing: dict[str, list[ET.Element]] = {}
    for flow in sequence_flows:
        outgoing.setdefault(flow.get("sourceRef", ""), []).append(flow)
    for gateway in root.findall(f".//{{{BPMN}}}exclusiveGateway"):
        default = gateway.get("default")
        if not default:
            errors.append(f"{path}: gateway {gateway.get('id')} has no default flow")
        for flow in outgoing.get(gateway.get("id", ""), []):
            if flow.get("id") != default and flow.find(f"{{{BPMN}}}conditionExpression") is None:
                errors.append(f"{path}: branch {flow.get('id')} has no condition")
    shapes = {shape.get("bpmnElement") for shape in root.findall(f".//{{{BPMNDI}}}BPMNShape")}
    edges = {edge.get("bpmnElement") for edge in root.findall(f".//{{{BPMNDI}}}BPMNEdge")}
    node_tags = {"participant", "task", "serviceTask", "userTask", "businessRuleTask", "sendTask", "receiveTask", "startEvent", "endEvent", "intermediateCatchEvent", "intermediateThrowEvent", "exclusiveGateway", "parallelGateway", "eventBasedGateway", "boundaryEvent", "dataStoreReference", "dataObjectReference"}
    for element in elements:
        if element.tag.rsplit("}", 1)[-1] in node_tags and element.get("id") not in shapes:
            errors.append(f"{path}: {element.get('id')} has no BPMNDI shape")
    for flow in sequence_flows + message_flows:
        if flow.get("id") not in edges:
            errors.append(f"{path}: {flow.get('id')} has no BPMNDI edge")
    return errors


def validate_repository(root: Path, config_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    schemas_dir = root / "models" / "schemas"
    schema_paths = sorted(schemas_dir.glob("*.schema.json"))
    schemas: dict[str, dict[str, Any]] = {}
    for path in schema_paths:
        schema = _load_json(path)
        schemas[path.name] = schema
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # jsonschema exposes several schema-error subclasses
            errors.append(f"{path}: invalid Draft 2020-12 schema: {exc}")

    version_path = root / "configs" / "uc4" / "schema_version.yaml"
    version_contract = yaml.safe_load(version_path.read_text(encoding="utf-8-sig"))
    if version_contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{version_path}: schema_version must be {SCHEMA_VERSION}")
    for field in ("config_schema", "entity_schema", "event_schema", "evidence_schema", "relationship_schema", "runtime_graph_schema", "integration_contract_schema", "artifact_manifest_schema", "migration_manifest"):
        declared = version_contract.get(field)
        if not isinstance(declared, str) or not (root / declared).is_file():
            errors.append(f"{version_path}: {field} does not resolve to a repository file: {declared!r}")

    config_raw = yaml.safe_load(config_path.read_text(encoding="utf-8-sig"))
    errors.extend(_json_errors(config_raw, schemas["simulation_config.schema.json"], str(config_path)))
    config: SimulationConfig | None = None
    try:
        config = SimulationConfig.model_validate(config_raw)
    except PydanticValidationError as exc:
        errors.extend(f"{config_path}:pydantic:{'.'.join(str(x) for x in item['loc'])}: {item['msg']}" for item in exc.errors())

    entity_path = root / "models" / "instances" / "uc4_entities.json"
    collection = _load_json(entity_path)
    entity_schema = schemas["entity.schema.json"]
    registry = Registry().with_resource(entity_schema["$id"], Resource.from_contents(entity_schema))
    errors.extend(_json_errors(collection, schemas["entity_collection.schema.json"], str(entity_path), registry))
    entities: dict[str, Entity] = {}
    for index, raw in enumerate(collection.get("entities", [])):
        try:
            entity = Entity.model_validate(raw)
            if entity.entity_id in entities:
                errors.append(f"{entity_path}: duplicate entity_id {entity.entity_id}")
            entities[entity.entity_id] = entity
            if Entity.model_validate_json(entity.model_dump_json(exclude_none=True)) != entity:
                errors.append(f"{entity_path}: entity {entity.entity_id} failed Pydantic JSON round-trip")
        except PydanticValidationError as exc:
            errors.append(f"{entity_path}:entities[{index}]: {exc}")

    inventory_path = root / "data" / "inventory" / "uc4_entity_inventory.csv"
    with inventory_path.open(encoding="utf-8-sig", newline="") as handle:
        inventory_ids = {row["entity_id"] for row in csv.DictReader(handle)}
    if inventory_ids != set(entities):
        errors.append(f"entity inventory/instance ID mismatch: missing_in_json={sorted(inventory_ids-set(entities))}, missing_in_csv={sorted(set(entities)-inventory_ids)}")

    relationship_path = root / "models" / "relationships" / "uc4_relationships.csv"
    relationships = load_relationships(relationship_path)
    relationship_ids: set[str] = set()
    for relation in relationships:
        errors.extend(_json_errors(relation, schemas["relationship.schema.json"], relation["relationship_id"]))
        if relation["relationship_id"] in relationship_ids:
            errors.append(f"duplicate relationship_id {relation['relationship_id']}")
        relationship_ids.add(relation["relationship_id"])
        for endpoint in (relation["source_entity"], relation["target_entity"]):
            if endpoint not in entities:
                errors.append(f"{relation['relationship_id']}: unresolved endpoint {endpoint}")
        if relation["valid_from"] is not None and relation["valid_to"] is not None and relation["valid_from"] >= relation["valid_to"]:
            errors.append(f"{relation['relationship_id']}: valid_from must be less than valid_to")

    graph = build_graph(collection, relationships)
    if graph.number_of_nodes() and not nx.is_connected(graph.to_undirected()):
        errors.append("UC4 relationship graph is not weakly connected")
    for entity in entities.values():
        if entity.twin_id:
            forward = graph.get_edge_data(entity.entity_id, entity.twin_id, default={})
            synchronization = graph.get_edge_data("UC4-S06", entity.twin_id, default={})
            if not any(data.get("relationship_type") == "MIRRORED_BY" for data in forward.values()):
                errors.append(f"missing MIRRORED_BY {entity.entity_id}->{entity.twin_id}")
            if not any(data.get("relationship_type") == "SYNCHRONIZES_WITH" for data in synchronization.values()):
                errors.append(f"missing SYNCHRONIZES_WITH UC4-S06->{entity.twin_id}")

    if config:
        unknown = set(config.topology.enabled_entities) - set(entities)
        if unknown:
            errors.append(f"{config_path}: unknown enabled entity IDs: {sorted(unknown)}")
        unknown_devices = set(config.devices) - set(entities)
        if unknown_devices:
            errors.append(f"{config_path}: unknown device profile IDs: {sorted(unknown_devices)}")
        for field, entity_id in (("entry_entity", config.incident.entry_entity), ("tamper_target", config.incident.tamper_target)):
            if entity_id not in config.topology.enabled_entities:
                errors.append(f"{config_path}: incident.{field} {entity_id} is not enabled")
        if "cpe_flow_metadata" in config.authorization.allowed_data_types and not config.network.logging_enabled:
            errors.append(f"{config_path}: cpe_flow_metadata acquisition requires network.logging_enabled=true")
        for source_id in config.reconstruction.source_reliability:
            if source_id not in entities:
                errors.append(f"{config_path}: unknown reconstruction source {source_id}")

    integration_path = root / "contracts" / "integration" / "uc4_integration_contracts.yaml"
    integration = yaml.safe_load(integration_path.read_text(encoding="utf-8-sig"))
    errors.extend(_json_errors(
        integration, schemas["integration_contracts.schema.json"], str(integration_path),
    ))
    contracts = integration.get("contracts", []) if isinstance(integration, dict) else []
    contract_ids = [item.get("contract_id") for item in contracts if isinstance(item, dict)]
    message_ids = [
        message.get("message_id")
        for contract in contracts if isinstance(contract, dict)
        for message in contract.get("messages", []) if isinstance(message, dict)
    ]
    if len(contract_ids) != len(set(contract_ids)):
        errors.append(f"{integration_path}: contract_id values must be unique")
    if len(message_ids) != len(set(message_ids)):
        errors.append(f"{integration_path}: message_id values must be unique")
    for contract in contracts:
        for message in contract.get("messages", []):
            schema_ref = message.get("schema_ref")
            if schema_ref and not (root / schema_ref).is_file():
                errors.append(f"{integration_path}: unresolved schema_ref {schema_ref}")

    bpmn_paths = sorted((root / "diagrams").rglob("*.bpmn"))
    for path in bpmn_paths:
        errors.extend(validate_bpmn(path))

    fixture_dir = root / "tests" / "fixtures" / "uc4"
    for name, schema_name, model in (
        ("event.valid.json", "event.schema.json", UC4Event),
        ("evidence.valid.json", "evidence.schema.json", EvidenceItem),
    ):
        path = fixture_dir / name
        raw = _load_json(path)
        errors.extend(_json_errors(raw, schemas[schema_name], str(path)))
        try:
            instance = model.model_validate(raw)
            if json.loads(instance.model_dump_json(exclude_none=True)) != raw:
                errors.append(f"{path}: Pydantic JSON round-trip changed the document")
        except PydanticValidationError as exc:
            errors.append(f"{path}:pydantic: {exc}")

    if errors:
        raise RepositoryValidationError(errors)
    report = {
        "config": str(config_path),
        "schema_version": SCHEMA_VERSION,
        "schemas": len(schema_paths),
        "entities": len(entities),
        "relationships": len(relationships),
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "bpmn_files": len(bpmn_paths),
        "integration_contracts": len(contracts),
        "round_trip_types": ["entity", "event", "evidence"],
        "status": "valid",
    }
    return report, graph_document(graph, sources=[entity_path, relationship_path])
