
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

TYPE_COLORS = {
    "organization": "#1f77b4",
    "position": "#ff7f0e",
    "person": "#2ca02c",
    "subdivision": "#d62728",
    "source": "#9467bd",
}

def plot_relation_counts(relation_counts: pd.DataFrame, output_path: Path):
    pivot = relation_counts.pivot(index="type", columns="layer", values="count").fillna(0)
    pivot = pivot.sort_values(by=list(pivot.columns), ascending=False)
    ax = pivot.plot(kind="barh", figsize=(10, 7))
    ax.set_title("Количество связей по слоям и типам")
    ax.set_xlabel("Число связей")
    ax.set_ylabel("Тип связи")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def plot_top_degree(centrality_table: pd.DataFrame, output_path: Path, top_n: int = 15):
    top = centrality_table.head(top_n).copy()
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top["label"][::-1], top["degree"][::-1])
    ax.set_title(f"Топ-{top_n} узлов formal core по степени")
    ax.set_xlabel("Степень узла")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def plot_network_top_nodes(graph: nx.Graph, centrality_table: pd.DataFrame, output_path: Path, top_n: int = 40):
    top_nodes = set(centrality_table.head(top_n)["kumu_id"])
    undirected = graph.to_undirected().subgraph(top_nodes).copy()
    pos = nx.spring_layout(undirected, seed=42, k=0.8)
    colors = [TYPE_COLORS.get(undirected.nodes[n].get("type"), "#7f7f7f") for n in undirected.nodes()]
    sizes = [100 + 60 * undirected.degree(n) for n in undirected.nodes()]
    labels = {n: undirected.nodes[n].get("label", n)[:28] for n in undirected.nodes()}

    fig, ax = plt.subplots(figsize=(14, 10))
    nx.draw_networkx_edges(undirected, pos, alpha=0.25, ax=ax, width=1)
    nx.draw_networkx_nodes(undirected, pos, node_color=colors, node_size=sizes, ax=ax)
    nx.draw_networkx_labels(undirected, pos, labels=labels, font_size=7, ax=ax)
    ax.set_title(f"Формальное ядро сети: {top_n} наиболее связанных узлов")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def plot_official_collection_counts(summary: pd.DataFrame, output_path: Path):
    if summary.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.set_title("Официальный сбор: данных нет")
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return
    pivot = summary.pivot(index="provider", columns="entity_group", values="count").fillna(0)
    ax = pivot.plot(kind="bar", figsize=(10, 6))
    ax.set_title("Автоматизированный сбор с официальных сайтов")
    ax.set_xlabel("Провайдер официальных данных")
    ax.set_ylabel("Количество записей")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
