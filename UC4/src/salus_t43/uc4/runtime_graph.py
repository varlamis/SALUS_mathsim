"""Construct the UC4 temporal graph from static and runtime model data."""

from __future__ import annotations

from collections import defaultdict
from html import escape
from typing import Any


def build_runtime_graph(
    run_id: str,
    static_graph: dict[str, Any],
    observed_events: list[dict[str, Any]],
    policy_decisions: list[dict[str, Any]],
    evidence_manifest: dict[str, Any],
    custody_events: list[dict[str, Any]],
    reconstruction: dict[str, Any],
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    edge_sequence = 0

    def add_node(node_id: str, node_type: str, attributes: dict[str, Any], valid_from: float | None = None, valid_to: float | None = None) -> None:
        candidate = {"id": node_id, "node_type": node_type, "valid_from": valid_from, "valid_to": valid_to, "attributes": attributes}
        if node_id in nodes and nodes[node_id] != candidate:
            if nodes[node_id]["node_type"] == "source_record" and node_type == "source_record":
                nodes[node_id]["attributes"].update(attributes)
                return
            raise ValueError(f"conflicting runtime graph node {node_id}")
        nodes[node_id] = candidate

    def add_edge(source: str, target: str, relationship_type: str, attributes: dict[str, Any] | None = None, valid_from: float | None = None, valid_to: float | None = None, edge_id: str | None = None) -> None:
        nonlocal edge_sequence
        edge_sequence += 1
        edges.append({
            "edge_id": edge_id or f"UC4-RTE-{edge_sequence:06d}",
            "source": source,
            "target": target,
            "relationship_type": relationship_type,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "attributes": dict(attributes or {}),
        })

    for static in static_graph["nodes"]:
        entity_id = static["entity_id"]
        add_node(entity_id, "static_entity", {key: value for key, value in static.items() if key != "entity_id"})
    for relation in static_graph["edges"]:
        add_edge(
            relation["source_entity"], relation["target_entity"], relation["relationship_type"],
            {key: value for key, value in relation.items() if key not in {"source_entity", "target_entity", "relationship_type", "valid_from", "valid_to", "relationship_id"}},
            relation.get("valid_from"), relation.get("valid_to"), relation["relationship_id"],
        )

    events_by_signature: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for event in observed_events:
        event_id = event["event_id"]
        event_time = event["event_time"]
        graph_time = event["ingest_time"]
        add_node(event_id, "event", event, graph_time, graph_time + 1e-9)
        add_edge(event["source_entity"], event_id, "GENERATES", {"visibility": event["visibility"], "reported_event_time": event_time}, graph_time, graph_time + 1e-9)
        signature = (event["event_type"], tuple(event.get("correlation_ids", [])))
        events_by_signature[signature].append(event_id)

    authorization_ids = sorted({item["authorization_id"] for item in policy_decisions} | {
        entry["item"]["authorization_id"] for entry in evidence_manifest.get("evidence", [])
    })
    for authorization_id in authorization_ids:
        add_node(authorization_id, "authorization", {"authorization_id": authorization_id})
        add_edge("UC4-A03", authorization_id, "GENERATES", {"runtime": True})

    for decision in policy_decisions:
        decision_id = decision["policy_decision_id"]
        evaluation_time = decision["evaluation_time"]
        add_node(decision_id, "policy_decision", decision, evaluation_time, evaluation_time + 1e-9)
        add_edge("UC4-S02", decision_id, "GENERATES", {"decision": decision["decision"]}, evaluation_time, evaluation_time + 1e-9)
        add_edge(decision_id, decision["authorization_id"], "AUTHORIZED_BY", {"outcome": decision["decision"]}, evaluation_time, evaluation_time + 1e-9)
        if decision.get("record_id"):
            add_node(decision["record_id"], "source_record", {"record_id": decision["record_id"], "collected": False})
            add_edge(decision["record_id"], decision_id, "CONTROLLED_BY", {"reason_code": decision["reason_code"]}, evaluation_time, evaluation_time + 1e-9)

    for entry in evidence_manifest.get("evidence", []):
        item = entry["item"]
        content = entry["content"]
        evidence_id = item["evidence_id"]
        add_node(evidence_id, "evidence", {**item, "content": content}, item["acquisition_time"])
        add_edge(evidence_id, item["authorization_id"], "AUTHORIZED_BY", {"policy_decision_id": item["policy_decision_id"]}, item["acquisition_time"])
        add_edge(evidence_id, item["policy_decision_id"], "CONTROLLED_BY", {"status": item["custody_status"]}, item["acquisition_time"])
        for record_id in item["source_record_ids"]:
            add_node(record_id, "source_record", {"record_id": record_id, "collected": True, "content": content}, content.get("event_time"))
            add_edge(evidence_id, record_id, "DERIVED_FROM", {"content_hash": item["content_hash"]}, item["acquisition_time"])
            source_entity = item["source_entity"]
            add_edge(source_entity, record_id, "GENERATES", {"data_origin": content.get("source")}, content.get("event_time"))
            signature = (content.get("event_type"), tuple(content.get("correlation_ids", [])))
            if events_by_signature.get(signature):
                add_edge(record_id, events_by_signature[signature][0], "DERIVED_FROM", {"match": "event_type_and_correlation"}, content.get("event_time"))

    evidence_ids = {entry["item"]["evidence_id"] for entry in evidence_manifest.get("evidence", [])}
    for custody in custody_events:
        custody_id = custody["custody_id"]
        action_time = custody["action_time"]
        add_node(custody_id, "custody_action", custody, action_time, action_time + 1e-9)
        add_edge("UC4-S04", custody_id, "GENERATES", {"action": custody["action"]}, action_time, action_time + 1e-9)
        if custody["evidence_id"] in evidence_ids:
            add_edge(custody["evidence_id"], custody_id, "CUSTODIED_BY", {"chain_hash": custody["chain_hash"]}, action_time, action_time + 1e-9)

    for claim in reconstruction.get("claims", []):
        claim_id = claim["claim_id"]
        interval = claim.get("time_interval") or {}
        add_node(claim_id, "claim", claim, interval.get("start"), interval.get("end"))
        add_edge("UC4-S05", claim_id, "GENERATES", {"qualification": claim["qualification"]}, interval.get("start"), interval.get("end"))
        for evidence_id in claim.get("evidence_ids", []):
            if evidence_id in evidence_ids:
                add_edge(claim_id, evidence_id, "CORRELATES_WITH", {"role": "support"}, interval.get("start"), interval.get("end"))

    node_ids = set(nodes)
    unresolved = [(edge["edge_id"], edge["source"], edge["target"]) for edge in edges if edge["source"] not in node_ids or edge["target"] not in node_ids]
    if unresolved:
        raise ValueError(f"runtime graph has unresolved endpoints: {unresolved[:3]}")
    if len({edge["edge_id"] for edge in edges}) != len(edges):
        raise ValueError("runtime graph edge IDs are not unique")
    static_count = sum(node["node_type"] == "static_entity" for node in nodes.values())
    return {
        "metadata": {
            "schema_version": "1.0.0", "use_case": "UC4", "run_id": run_id,
            "directed": True, "multigraph": True, "ground_truth_included": False,
            "static_node_count": static_count, "runtime_node_count": len(nodes) - static_count,
        },
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(edges, key=lambda item: item["edge_id"]),
    }


def render_graph_overview(graph: dict[str, Any]) -> str:
    """Return a deterministic, compact SVG summary rather than an unreadable full graph."""
    counts: dict[str, int] = defaultdict(int)
    for node in graph["nodes"]:
        counts[node["node_type"]] += 1
    layers = [
        ("static_entity", "Canonical entities"), ("event", "Observed events"),
        ("policy_decision", "Policy decisions"), ("evidence", "Evidence"),
        ("custody_action", "Custody actions"), ("claim", "Claims"),
    ]
    width, height = 1120, 250
    box_width, box_height, y = 150, 74, 85
    positions = [30 + index * 182 for index in range(len(layers))]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#52606d"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<text x="30" y="35" font-family="sans-serif" font-size="20" font-weight="bold" fill="#102a43">UC4 temporal graph overview</text>',
        f'<text x="30" y="58" font-family="sans-serif" font-size="12" fill="#486581">{escape(graph["metadata"]["run_id"])} · hidden ground truth excluded</text>',
    ]
    for left, right in zip(positions, positions[1:]):
        parts.append(f'<line x1="{left + box_width}" y1="{y + box_height / 2}" x2="{right - 8}" y2="{y + box_height / 2}" stroke="#52606d" stroke-width="2" marker-end="url(#arrow)"/>')
    for x, (key, label) in zip(positions, layers):
        parts.extend([
            f'<rect x="{x}" y="{y}" width="{box_width}" height="{box_height}" rx="8" fill="#d9eaf7" stroke="#3273a8"/>',
            f'<text x="{x + box_width / 2}" y="{y + 29}" text-anchor="middle" font-family="sans-serif" font-size="13" fill="#102a43">{escape(label)}</text>',
            f'<text x="{x + box_width / 2}" y="{y + 56}" text-anchor="middle" font-family="sans-serif" font-size="22" font-weight="bold" fill="#0b5d8b">{counts[key]}</text>',
        ])
    parts.append(f'<text x="30" y="220" font-family="sans-serif" font-size="12" fill="#486581">Edges: {len(graph["edges"])} · Source records: {counts["source_record"]} · Authorizations: {counts["authorization"]}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
