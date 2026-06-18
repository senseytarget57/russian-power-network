from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.load_data import build_processed_tables
from src.build_graphs import build_core_formal_graph
from src.metrics import compute_centrality_table, summarize_layers, relation_count_by_layer, summarize_official_collection
from src.plots import plot_relation_counts, plot_top_degree, plot_network_top_nodes, plot_official_collection_counts
from src.scrape_official import collect_official_snapshot

OUT_FIG = BASE_DIR / "outputs" / "figures"
OUT_TAB = BASE_DIR / "outputs" / "tables"


def main():
    OUT_TAB.mkdir(parents=True, exist_ok=True)
    OUT_FIG.mkdir(parents=True, exist_ok=True)

    # 1. Автоматизированный сбор/загрузка официального институционального слоя.
    official_snapshot = collect_official_snapshot(prefer_live=True, save_processed=True)
    official_summary = summarize_official_collection(official_snapshot)
    official_snapshot.to_csv(OUT_TAB / "official_snapshot.csv", index=False)
    official_summary.to_csv(OUT_TAB / "official_collection_summary.csv", index=False)
    plot_official_collection_counts(official_summary, OUT_FIG / "official_collection_counts.png")

    # 2. Основной анализ многослойной сети.
    nodes, edges = build_processed_tables(save=True)

    core_graph = build_core_formal_graph(nodes, edges)
    centrality = compute_centrality_table(core_graph)
    summary = summarize_layers(nodes, edges)
    relation_counts = relation_count_by_layer(edges)

    centrality.to_csv(OUT_TAB / "core_formal_centrality.csv", index=False)
    summary.to_csv(OUT_TAB / "summary_stats.csv", index=False)
    relation_counts.to_csv(OUT_TAB / "relation_counts_by_layer.csv", index=False)

    plot_relation_counts(relation_counts, OUT_FIG / "relations_by_layer.png")
    plot_top_degree(centrality, OUT_FIG / "top15_core_degree.png", top_n=15)
    plot_network_top_nodes(core_graph, centrality, OUT_FIG / "core_network_top40.png", top_n=40)

    print("Done.")
    print("Nodes:", nodes.shape[0], "Edges:", edges.shape[0])
    print("Official snapshot rows:", official_snapshot.shape[0])


if __name__ == "__main__":
    main()
