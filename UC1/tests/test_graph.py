import networkx as nx

from salus_t43.uc1.graph import competency_queries, runtime_graph, static_graph
from salus_t43.uc1.simulation import run_simulation


def test_graph_is_connected_and_preserves_parallel_ids(repo_root):
    graph = static_graph(repo_root)
    assert isinstance(graph, nx.MultiDiGraph)
    assert graph.number_of_nodes() == 30
    assert graph.number_of_edges() == 60
    assert nx.is_connected(graph.to_undirected())
    assert len({key for _u, _v, key in graph.edges(keys=True)}) == 60


def test_every_declared_twin_mapping_exists(repo_root):
    graph = static_graph(repo_root)
    for device, twin in {"UC1-D01":"UC1-DT01", "UC1-D02":"UC1-DT02", "UC1-D05":"UC1-DT05", "UC1-D06":"UC1-DT06"}.items():
        assert any(row["relationship_type"] == "MIRRORED_BY" for row in graph.get_edge_data(device, twin).values())


def test_runtime_queries_exclude_truth(repo_root):
    result = run_simulation(repo_root, repo_root / "configs/uc1/forged_message_attack.yaml")
    graph = result.documents["graph"]
    assert graph["metadata"]["hidden_truth_excluded"] is True
    assert "ground_truth" not in str(graph)
    queries = competency_queries(graph)
    assert queries["attack_surface"] == ["UC1-D08"]
    assert queries["trust_validators"] == ["UC1-S02"]

