"""Data-driven competency queries over a UC4 temporal graph document."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


class CompetencyQueryEngine:
    def __init__(self, graph: dict[str, Any]) -> None:
        self.graph = graph
        self.nodes = {node["id"]: node for node in graph["nodes"]}
        self.edges = graph["edges"]

    def physical_devices_and_twins(self) -> dict[str, Any]:
        rows = []
        for node in self._static_entities():
            attributes = node["attributes"]
            twin_id = attributes.get("twin_id")
            if attributes.get("designation") == "physical" and twin_id:
                twin = self.nodes.get(twin_id)
                rows.append({
                    "physical_entity_id": node["id"], "physical_name": attributes.get("name"),
                    "twin_entity_id": twin_id, "twin_name": twin["attributes"].get("name") if twin else None,
                })
        return {"question": "Which UC4 physical devices and digital twins exist?", "count": len(rows), "results": rows}

    def home_lan_routing(self) -> dict[str, Any]:
        gateways = {
            node["id"] for node in self._static_entities()
            if "routing" in node["attributes"].get("capabilities", [])
        }
        memberships: dict[str, set[str]] = {}
        for edge in self.edges:
            if edge["relationship_type"] == "MEMBER_OF_ZONE":
                memberships.setdefault(edge["target"], set()).add(edge["source"])
        candidate_zones = {
            zone for zone, members in memberships.items()
            if members & gateways and sum(
                self.nodes[item]["attributes"].get("designation") == "physical"
                for item in members if item in self.nodes
            ) >= 2
        }
        routes = [edge for edge in self.edges if edge["relationship_type"] == "ROUTES_THROUGH" and edge["target"] in gateways]
        rows = []
        for edge in routes:
            zones = sorted(zone for zone in candidate_zones if edge["source"] in memberships[zone])
            if zones:
                rows.append({"entity_id": edge["source"], "zone_ids": zones, "routing_gateway_id": edge["target"]})
        return {"question": "Which entities are on the home LAN and route through the CPE?", "count": len(rows), "results": rows}

    def source_artifacts(self) -> dict[str, Any]:
        source_classes = {"NetworkFlowLogEntry", "EventLogEntry", "EventTelemetry"}
        rows = []
        for node in self._static_entities():
            if node["attributes"].get("entity_class") not in source_classes:
                continue
            generators = sorted({
                edge["source"] for edge in self.edges
                if edge["target"] == node["id"] and edge["relationship_type"] == "GENERATES"
            })
            data_types = sorted({
                data_type
                for edge in self.edges
                if edge["target"] == node["id"] and edge["relationship_type"] == "GENERATES"
                for data_type in edge["attributes"].get("attributes", {}).get("data_types", [])
            })
            rows.append({
                "artifact_entity_id": node["id"], "name": node["attributes"].get("name"),
                "entity_class": node["attributes"].get("entity_class"), "generated_by": generators,
                "data_types": data_types,
            })
        return {"question": "Which source artefacts can contain evidence of entry or tampering?", "count": len(rows), "results": rows}

    def evidence_provenance(self) -> dict[str, Any]:
        rows = []
        for node in self._nodes_of_type("evidence"):
            evidence_id = node["id"]
            records = self._targets(evidence_id, "DERIVED_FROM", "source_record")
            source_entities = sorted({source for record in records for source in self._sources(record, "GENERATES", "static_entity")})
            rows.append({
                "evidence_id": evidence_id,
                "custody_status": node["attributes"].get("custody_status"),
                "source_record_ids": records,
                "source_entity_ids": source_entities,
                "authorization_ids": self._targets(evidence_id, "AUTHORIZED_BY", "authorization"),
                "policy_decision_ids": self._targets(evidence_id, "CONTROLLED_BY", "policy_decision"),
                "custody_action_ids": self._targets(evidence_id, "CUSTODIED_BY", "custody_action"),
            })
        return {"question": "Which evidence items derive from which source artefacts and entities?", "count": len(rows), "results": rows}

    def evidence_authorizations(self) -> dict[str, Any]:
        rows = []
        for node in self._nodes_of_type("evidence"):
            rows.append({
                "evidence_id": node["id"],
                "authorization_ids": self._targets(node["id"], "AUTHORIZED_BY", "authorization"),
                "policy_decision_ids": self._targets(node["id"], "CONTROLLED_BY", "policy_decision"),
            })
        return {"question": "Which authorization permitted each collected item?", "count": len(rows), "results": rows}

    def policy_outcomes(self) -> dict[str, Any]:
        rows = []
        for node in self._nodes_of_type("policy_decision"):
            attributes = node["attributes"]
            rows.append({
                "policy_decision_id": node["id"], "record_id": attributes.get("record_id"),
                "decision": attributes.get("decision"), "reason_code": attributes.get("reason_code"),
                "authorization_id": attributes.get("authorization_id"),
                "bytes_released": attributes.get("bytes_released"),
            })
        return {"question": "Which requests were denied, minimized, expired, or revoked, and why?", "count": len(rows), "results": rows}

    def claim_support(self) -> dict[str, Any]:
        rows = []
        for node in self._nodes_of_type("claim"):
            evidence_ids = self._targets(node["id"], "CORRELATES_WITH", "evidence")
            observation_ids = sorted({
                event_id
                for evidence_id in evidence_ids
                for record_id in self._targets(evidence_id, "DERIVED_FROM", "source_record")
                for event_id in self._targets(record_id, "DERIVED_FROM", "event")
            })
            rows.append({
                "claim_id": node["id"], "claim_type": node["attributes"].get("claim_type"),
                "qualification": node["attributes"].get("qualification"),
                "evidence_ids": evidence_ids, "observation_event_ids": observation_ids,
            })
        return {"question": "Which observations support each reconstructed claim?", "count": len(rows), "results": rows}

    def assumptions_and_tbd(self) -> dict[str, Any]:
        rows = []
        for node in self._static_entities():
            provenance = node["attributes"].get("provenance", {})
            if provenance.get("record_status") in {"assumed", "TBD"} or provenance.get("assumption_ids"):
                rows.append({
                    "object_type": "entity", "object_id": node["id"],
                    "record_status": provenance.get("record_status"),
                    "assumption_ids": provenance.get("assumption_ids", []),
                })
            for interface in node["attributes"].get("interfaces", []):
                if interface.get("status") == "TBD" or "TBD" in interface.get("protocol", ""):
                    rows.append({
                        "object_type": "interface", "object_id": f"{node['id']}:{interface.get('name')}",
                        "record_status": interface.get("status"), "assumption_ids": provenance.get("assumption_ids", []),
                    })
        for edge in self.edges:
            status = edge["attributes"].get("record_status")
            assumptions = edge["attributes"].get("assumption_ids", [])
            if status in {"assumed", "TBD"} or assumptions:
                rows.append({"object_type": "relationship", "object_id": edge["edge_id"], "record_status": status, "assumption_ids": assumptions})
        return {"question": "Which relations or attributes are assumed/TBD rather than confirmed?", "count": len(rows), "results": rows}

    def service_feeds(self) -> dict[str, Any]:
        rows = []
        category_count = {"detection": 0, "evidence": 0, "digital_twin": 0, "sdn": 0}
        for node in self._static_entities():
            attributes = node["attributes"]
            if not attributes.get("entity_class", "").endswith("Service"):
                continue
            capabilities = " ".join(attributes.get("capabilities", [])).lower()
            categories = []
            if "detect" in capabilities or "anomaly" in capabilities:
                categories.append("detection")
            if any(token in capabilities for token in ("evidence", "storage", "custody", "hash_verification")):
                categories.append("evidence")
            if "twin" in capabilities:
                categories.append("digital_twin")
            if "sdn" in capabilities:
                categories.append("sdn")
            for category in categories:
                category_count[category] += 1
                feeds = {
                    edge["source"] for edge in self.edges
                    if edge["target"] == node["id"]
                    and edge["relationship_type"] in {"OBSERVED_BY", "COLLECTED_BY", "CUSTODIED_BY", "PRODUCES_EVIDENCE"}
                }
                feeds.update(self._targets(node["id"], "CONSUMES", None))
                rows.append({"category": category, "service_id": node["id"], "service_name": attributes.get("name"), "feed_entity_ids": sorted(feeds)})
        gaps = [f"No enabled service declares a {category} capability." for category, count in category_count.items() if count == 0]
        return {"question": "Which entities feed detection, evidence, Digital Twin, or SDN services?", "count": len(rows), "results": rows, "explicit_gaps": gaps}

    def run(self, query_name: str = "all") -> dict[str, Any]:
        queries: dict[str, Callable[[], dict[str, Any]]] = {
            "physical_devices_and_twins": self.physical_devices_and_twins,
            "home_lan_routing": self.home_lan_routing,
            "source_artifacts": self.source_artifacts,
            "evidence_provenance": self.evidence_provenance,
            "evidence_authorizations": self.evidence_authorizations,
            "policy_outcomes": self.policy_outcomes,
            "claim_support": self.claim_support,
            "assumptions_and_tbd": self.assumptions_and_tbd,
            "service_feeds": self.service_feeds,
        }
        if query_name != "all":
            if query_name not in queries:
                raise KeyError(f"unknown competency query {query_name!r}; choose from {sorted(queries)}")
            return {"schema_version": "1.0.0", "graph_run_id": self.graph["metadata"]["run_id"], "queries": {query_name: queries[query_name]()}}
        return {"schema_version": "1.0.0", "graph_run_id": self.graph["metadata"]["run_id"], "queries": {name: query() for name, query in queries.items()}}

    def _static_entities(self) -> list[dict[str, Any]]:
        return self._nodes_of_type("static_entity")

    def _nodes_of_type(self, node_type: str) -> list[dict[str, Any]]:
        return [node for node in self.graph["nodes"] if node["node_type"] == node_type]

    def _targets(self, source: str, relationship_type: str | None, node_type: str | None) -> list[str]:
        return sorted({
            edge["target"] for edge in self.edges
            if edge["source"] == source
            and (relationship_type is None or edge["relationship_type"] == relationship_type)
            and (node_type is None or self.nodes[edge["target"]]["node_type"] == node_type)
        })

    def _sources(self, target: str, relationship_type: str | None, node_type: str | None) -> list[str]:
        return sorted({
            edge["source"] for edge in self.edges
            if edge["target"] == target
            and (relationship_type is None or edge["relationship_type"] == relationship_type)
            and (node_type is None or self.nodes[edge["source"]]["node_type"] == node_type)
        })


def load_graph(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
