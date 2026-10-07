import json
import xml.etree.ElementTree as ET

from jsonschema import Draft202012Validator

from salus_mathsim.uc4.queries import CompetencyQueryEngine
from salus_mathsim.uc4.simulation import run_simulation


def _result(repo_root):
    return run_simulation(repo_root, repo_root / "configs" / "uc4" / "incident_lawful_access.yaml")


def test_runtime_graph_validates_and_excludes_hidden_truth(repo_root):
    result = _result(repo_root)
    graph = result.documents["graph"]
    schema = json.loads((repo_root / "models" / "schemas" / "runtime_graph.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(graph)) == []
    node_ids = {node["id"] for node in graph["nodes"]}
    assert graph["metadata"]["ground_truth_included"] is False
    assert not ({event["event_id"] for event in result.documents["ground_truth_events"]} - {event["event_id"] for event in result.documents["observed_events"]}) & node_ids
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in graph["edges"])
    assert len({edge["edge_id"] for edge in graph["edges"]}) == len(graph["edges"])


def test_competency_queries_resolve_required_paths(repo_root):
    result = _result(repo_root)
    queries = CompetencyQueryEngine(result.documents["graph"]).run()["queries"]
    assert queries["physical_devices_and_twins"]["count"] == 6
    assert queries["home_lan_routing"]["count"] == 5
    assert queries["source_artifacts"]["count"] == 3
    assert queries["evidence_provenance"]["count"] == 17
    assert queries["claim_support"]["count"] == 3
    assert all(row["authorization_ids"] for row in queries["evidence_provenance"]["results"])
    assert all(row["source_record_ids"] and row["custody_action_ids"] for row in queries["evidence_provenance"]["results"])
    assert all(row["evidence_ids"] and row["observation_event_ids"] for row in queries["claim_support"]["results"])
    assert any("detection" in gap for gap in queries["service_feeds"]["explicit_gaps"])
    assert any("sdn" in gap for gap in queries["service_feeds"]["explicit_gaps"])


def test_graph_overview_is_well_formed_svg(repo_root):
    svg = _result(repo_root).documents["graph_overview_svg"]
    root = ET.fromstring(svg)
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert "hidden ground truth excluded" in svg
