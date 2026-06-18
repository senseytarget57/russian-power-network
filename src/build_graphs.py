
import networkx as nx
import pandas as pd

FORMAL_TYPES = ["подчинение", "назначение", "занимает_должность"]

def build_graph(nodes: pd.DataFrame, edges: pd.DataFrame, node_layer=None, edge_layer=None, relation_types=None, directed=True):
    if node_layer is not None:
        nodes = nodes[nodes["layer"] == node_layer].copy()
    if edge_layer is not None:
        edges = edges[edges["layer"] == edge_layer].copy()
    if relation_types is not None:
        edges = edges[edges["type"].isin(relation_types)].copy()

    graph = nx.DiGraph() if directed else nx.Graph()

    node_ids = set(nodes["kumu_id"])
    for _, row in nodes.iterrows():
        attrs = row.dropna().to_dict()
        node_id = attrs.pop("kumu_id")
        graph.add_node(node_id, **attrs)

    for _, row in edges.iterrows():
        src = row["from"]
        tgt = row["to"]
        if src in node_ids and tgt in node_ids:
            attrs = row.dropna().to_dict()
            graph.add_edge(src, tgt, **attrs)

    return graph

def build_core_formal_graph(nodes: pd.DataFrame, edges: pd.DataFrame):
    return build_graph(nodes, edges, node_layer="core", edge_layer="core", relation_types=FORMAL_TYPES, directed=True)
