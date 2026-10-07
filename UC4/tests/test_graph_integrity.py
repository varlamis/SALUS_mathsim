import json

import networkx as nx

from salus_t43.graph_builder import build_graph, load_relationships, source_digest


def test_graph_is_connected_and_preserves_parallel_edge_ids(repo_root):
    collection = json.loads((repo_root / "models" / "instances" / "uc4_entities.json").read_text(encoding="utf-8"))
    relationships = load_relationships(repo_root / "models" / "relationships" / "uc4_relationships.csv")
    graph = build_graph(collection, relationships)
    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_nodes() == 38
    assert graph.number_of_edges() == 123
    assert nx.is_connected(graph.to_undirected())
    assert {key for _u, _v, key in graph.edges(keys=True)} == {r["relationship_id"] for r in relationships}


def test_every_physical_device_has_reciprocal_twin_links(repo_root):
    collection = json.loads((repo_root / "models" / "instances" / "uc4_entities.json").read_text(encoding="utf-8"))
    graph = build_graph(collection, load_relationships(repo_root / "models" / "relationships" / "uc4_relationships.csv"))
    devices = [entity for entity in collection["entities"] if entity.get("twin_id")]
    assert len(devices) == 6
    for entity in devices:
        forward = graph.get_edge_data(entity["entity_id"], entity["twin_id"])
        synchronization = graph.get_edge_data("UC4-S06", entity["twin_id"])
        assert any(data["relationship_type"] == "MIRRORED_BY" for data in forward.values())
        assert any(data["relationship_type"] == "SYNCHRONIZES_WITH" for data in synchronization.values())


def test_generated_graph_matches_canonical_sources(repo_root):
    entity_path = repo_root / "models" / "instances" / "uc4_entities.json"
    relationship_path = repo_root / "models" / "relationships" / "uc4_relationships.csv"
    document = json.loads((repo_root / "models" / "graph" / "uc4_graph.json").read_text(encoding="utf-8"))
    assert document["metadata"]["source_sha256"] == source_digest(entity_path, relationship_path)
    assert len(document["nodes"]) == 38
    assert len(document["edges"]) == 123
    assert len({node["entity_id"] for node in document["nodes"]}) == 38
    assert len({edge["relationship_id"] for edge in document["edges"]}) == 123
