from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import networkx as nx


def load_entities(root: Path) -> dict[str, Any]:
    return json.loads((root / "models/instances/uc1_entities.json").read_text(encoding="utf-8"))


def load_relationships(root: Path) -> list[dict[str, Any]]:
    with (root / "models/relationships/uc1_relationships.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["source_references"] = [x for x in row["source_references"].split(";") if x]
        row["assumption_ids"] = [x for x in row["assumption_ids"].split(";") if x]
    return rows


def static_graph(root: Path) -> nx.MultiDiGraph:
    collection = load_entities(root)
    graph = nx.MultiDiGraph(use_case="UC1", schema_version=collection["schema_version"])
    for entity in collection["entities"]:
        graph.add_node(entity["entity_id"], **entity)
    for relation in load_relationships(root):
        graph.add_edge(relation["source_entity"], relation["target_entity"], key=relation["relationship_id"], **relation)
    return graph


def static_document(root: Path) -> dict[str, Any]:
    graph = static_graph(root)
    return {
        "metadata": {"schema_version": "1.0.0", "use_case": "UC1", "hidden_truth_excluded": True, "directed": True, "multigraph": True},
        "nodes": [{"entity_id": node, **data} for node, data in sorted(graph.nodes(data=True))],
        "edges": [{"source_entity": source, "target_entity": target, **data} for source, target, _key, data in sorted(graph.edges(keys=True, data=True), key=lambda row: row[3]["relationship_id"])],
    }


def runtime_graph(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    graph = static_graph(root)
    nodes = [{"entity_id": node, **data} for node, data in sorted(graph.nodes(data=True))]
    edges = [{"source_entity": source, "target_entity": target, **data} for source, target, _key, data in sorted(graph.edges(keys=True, data=True), key=lambda row: row[3]["relationship_id"])]
    for alert in result["alerts"]:
        node_id = alert["event_id"]
        nodes.append({"entity_id": node_id, "entity_class": "RuntimeAlert", "score": alert["attributes"]["score"]})
        edges.append({"relationship_id": f"RUNTIME-{node_id}", "source_entity": "UC1-S03", "target_entity": node_id, "relationship_type": "GENERATES"})
    return {"metadata": {"schema_version": "1.0.0", "use_case": "UC1", "hidden_truth_excluded": True}, "nodes": nodes, "edges": edges}


def competency_queries(graph: dict[str, Any]) -> dict[str, Any]:
    nodes = graph["nodes"]
    edges = graph["edges"]
    return {
        "physical_and_twins": sorted(n["entity_id"] for n in nodes if n.get("designation") in {"physical", "digital"}),
        "message_path": ["UC1-D02", "UC1-NZ02", "UC1-D05", "UC1-D06", "UC1-D07"],
        "attack_surface": sorted(e["source_entity"] for e in edges if e.get("relationship_type") == "TARGETS"),
        "trust_validators": sorted(e["target_entity"] for e in edges if e.get("relationship_type") == "VALIDATED_BY"),
        "mitigation_points": sorted(e["target_entity"] for e in edges if e.get("relationship_type") == "MITIGATED_BY"),
        "assumed_entities": sorted(n["entity_id"] for n in nodes if n.get("record_status") in {"assumed", "TBD", "synthetic_default"}),
    }
