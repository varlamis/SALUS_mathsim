from salus_t43.uc3.graph import competency_queries, static_document


def test_graph_integrity_and_queries(repo_root):
    graph = static_document(repo_root)
    ids = {n["entity_id"] for n in graph["nodes"]}
    assert len(ids) == 36
    assert all(e["source_id"] in ids and e["target_id"] in ids for e in graph["edges"])
    queries = competency_queries(graph)
    assert "UC3-D05" in queries["plc_observers"] or "UC3-D10" in queries["plc_observers"]
    assert queries["plc_attackers"] == ["UC3-D11"]
    assert len(queries["digital_twins"]) == 9


def test_static_graph_has_source_digests(repo_root):
    graph = static_document(repo_root)
    assert all(len(value) == 64 for value in graph["source_digests"].values())
