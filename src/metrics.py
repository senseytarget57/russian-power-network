
import pandas as pd
import networkx as nx

def compute_centrality_table(graph: nx.Graph) -> pd.DataFrame:
    undirected = graph.to_undirected()
    degree_c = nx.degree_centrality(undirected)
    betweenness_c = nx.betweenness_centrality(undirected)
    closeness_c = nx.closeness_centrality(undirected)

    rows = []
    for node, attrs in graph.nodes(data=True):
        rows.append(
            {
                "kumu_id": node,
                "label": attrs.get("label", node),
                "node_type": attrs.get("type"),
                "contour": attrs.get("contour"),
                "degree": undirected.degree(node),
                "degree_centrality": degree_c.get(node, 0.0),
                "betweenness_centrality": betweenness_c.get(node, 0.0),
                "closeness_centrality": closeness_c.get(node, 0.0),
            }
        )

    return pd.DataFrame(rows).sort_values("degree_centrality", ascending=False)

def summarize_layers(nodes: pd.DataFrame, edges: pd.DataFrame) -> pd.DataFrame:
    summary = {
        "nodes_total": int(nodes.shape[0]),
        "edges_total": int(edges.shape[0]),
    }
    for layer in sorted(nodes["layer"].dropna().unique()):
        summary[f"{layer}_nodes"] = int((nodes["layer"] == layer).sum())
    for layer in sorted(edges["layer"].dropna().unique()):
        summary[f"{layer}_edges"] = int((edges["layer"] == layer).sum())
    return pd.DataFrame([summary])

def relation_count_by_layer(edges: pd.DataFrame) -> pd.DataFrame:
    return edges.groupby(["layer", "type"]).size().reset_index(name="count")


def summarize_official_collection(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["provider", "entity_group", "count"])
    return df.groupby(["provider", "entity_group"]).size().reset_index(name="count")
