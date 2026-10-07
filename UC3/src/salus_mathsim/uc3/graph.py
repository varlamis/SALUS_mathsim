import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def load_entities(root: Path) -> dict[str, Any]:
    return json.loads((root / "models/instances/uc3_entities.json").read_text(encoding="utf-8"))


def load_relationships(root: Path) -> list[dict[str, str]]:
    with (root / "models/relationships/uc3_relationships.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def static_document(root: Path) -> dict[str, Any]:
    entities = load_entities(root)
    edges = load_relationships(root)
    sources = {
        "entities_sha256": hashlib.sha256((root / "models/instances/uc3_entities.json").read_bytes()).hexdigest(),
        "relationships_sha256": hashlib.sha256((root / "models/relationships/uc3_relationships.csv").read_bytes()).hexdigest(),
    }
    return {"schema_version": "1.0.0", "use_case": "UC3", "source_digests": sources, "nodes": entities["entities"], "edges": edges}


def runtime_graph(root: Path, core: dict[str, Any]) -> dict[str, Any]:
    graph = static_document(root)
    runtime_nodes = []
    runtime_edges = []
    for group, prefix in (("alerts", "alert"), ("policy_decisions", "policy"), ("mitigation_actions", "mitigation"), ("evidence_manifest", "evidence")):
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
        "plc_attackers": sorted(e["source_id"] for e in edges if e.get("relationship_type") == "targets" and e.get("target_id") == "UC3-D05"),
        "plc_observers": sorted(e["source_id"] for e in edges if e.get("relationship_type") == "observes" and e.get("target_id") == "UC3-D05"),
        "evidence_sources": sorted({e["source_id"] for e in edges if e.get("relationship_type") == "generates" and str(e.get("target_id", "")).startswith(("UC3-S03", "UC3-ED"))}),
        "assumed_entities": sorted(n["entity_id"] for n in nodes if n.get("record_status") in {"assumed", "synthetic_default", "TBD"}),
    }
