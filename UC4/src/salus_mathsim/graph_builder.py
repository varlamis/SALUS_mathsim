"""Build the directed attributed UC4 multigraph from canonical model files."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import networkx as nx

from salus_mathsim import __version__


def _list_value(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[|;]", value) if part.strip()]


def relationship_row(row: dict[str, str]) -> dict[str, Any]:
    """Convert one canonical CSV row into the relationship JSON contract."""
    return {
        "schema_version": row["schema_version"],
        "relationship_id": row["relationship_id"],
        "use_case": row["use_case"],
        "source_entity": row["source_entity"],
        "target_entity": row["target_entity"],
        "relationship_type": row["relationship_type"],
        "description": row["description"],
        "valid_from": float(row["valid_from"]) if row["valid_from"].strip() else None,
        "valid_to": float(row["valid_to"]) if row["valid_to"].strip() else None,
        "confidence": row["confidence"],
        "record_status": row["record_status"],
        "source_references": _list_value(row["source_references"]),
        "assumption_ids": _list_value(row["assumption_ids"]),
        "attributes": {
            "interface": row["interface"],
            "protocol": row["protocol"],
            "authorization_relevance": row["authorization_relevance"],
            "data_types": _list_value(row["data_types"]),
            "notes": row["notes"],
        },
    }


def load_relationships(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [relationship_row(row) for row in csv.DictReader(handle)]


def build_graph(entity_collection: dict[str, Any], relationships: list[dict[str, Any]]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph(use_case="UC4", schema_version=entity_collection["schema_version"])
    for entity in entity_collection["entities"]:
        attributes = dict(entity)
        entity_id = attributes.pop("entity_id")
        graph.add_node(entity_id, **attributes)
    for rel in relationships:
        attributes = dict(rel)
        source = attributes.pop("source_entity")
        target = attributes.pop("target_entity")
        key = attributes["relationship_id"]
        graph.add_edge(source, target, key=key, **attributes)
    return graph


def source_digest(*paths: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def graph_document(graph: nx.MultiDiGraph, *, sources: list[Path]) -> dict[str, Any]:
    return {
        "metadata": {
            "schema_version": graph.graph["schema_version"],
            "use_case": graph.graph["use_case"],
            "generator": f"salus-mathsim {__version__}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_sha256": source_digest(*sources),
            "directed": True,
            "multigraph": True,
        },
        "nodes": [{"entity_id": node_id, **data} for node_id, data in sorted(graph.nodes(data=True))],
        "edges": [
            {"source_entity": source, "target_entity": target, **data}
            for source, target, _key, data in sorted(graph.edges(keys=True, data=True), key=lambda item: item[3]["relationship_id"])
        ],
    }


def write_graph(document: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
