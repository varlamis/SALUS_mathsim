import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def load_entities(root: Path) -> dict[str, Any]:
    return json.loads((root / "models/instances/uc5_entities.json").read_text(encoding="utf-8"))


def load_relationships(root: Path) -> list[dict[str, str]]:
    with (root / "models/relationships/uc5_relationships.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def static_document(root: Path) -> dict[str, Any]:
    entities = load_entities(root)
    edges = load_relationships(root)
    sources = {
        "entities_sha256": hashlib.sha256((root / "models/instances/uc5_entities.json").read_bytes()).hexdigest(),
        "relationships_sha256": hashlib.sha256((root / "models/relationships/uc5_relationships.csv").read_bytes()).hexdigest(),
    }
    return {"schema_version": "1.0.0", "use_case": "UC5", "source_digests": sources, "nodes": entities["entities"], "edges": edges}


def runtime_graph(root: Path, core: dict[str, Any]) -> dict[str, Any]:
    graph = static_document(root)
    runtime_nodes = []
    runtime_edges = []
    for group, prefix in (("alerts", "alert"), ("safety_decisions", "safety"), ("policy_decisions", "policy"), ("mitigation_actions", "mitigation"), ("evidence_manifest", "evidence")):
        for row in core[group]:
            node_id = row.get("event_id", row.get("evidence_id"))
            runtime_nodes.append({"entity_id": node_id, "entity_class": prefix, "runtime": True})
            source = row.get("source_entity") or row.get("source_event_id")
            if source:
                runtime_edges.append({"source_id": source, "relationship_type": "generates", "target_id": node_id})
    graph["nodes"] = graph["nodes"] + runtime_nodes
    graph["edges"] = graph["edges"] + runtime_edges
    return graph


def competency_queries(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph["nodes"]
    edges = graph["edges"]
    return {
        "physical_entities": sorted(n["entity_id"] for n in nodes if n.get("designation") == "physical"),
        "digital_twins": sorted(n["entity_id"] for n in nodes if n.get("entity_class") == "DigitalTwin"),
        "patient_monitor_observers": sorted(e["source_id"] for e in edges if e.get("relationship_type") == "observes" and e.get("target_id") == "UC5-D01"),
        "clinical_safety_services": sorted(n["entity_id"] for n in nodes if n.get("entity_class") == "PolicyService"),
        "evidence_sources": sorted({e["source_id"] for e in edges if e.get("relationship_type") == "generates" and str(e.get("target_id", "")).startswith(("UC5-S03", "UC5-ED"))}),
        "assumed_entities": sorted(n["entity_id"] for n in nodes if n.get("record_status") in {"assumed", "synthetic_default", "TBD"}),
    }

