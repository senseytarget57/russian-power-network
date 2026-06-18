
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

RAW_FILES = {
    "core_elements": "kumu_core_elements_import_type.csv",
    "core_connections": "kumu_core_connections_import_type.csv",
    "overlay_elements": "kumu_overlay_elements_import_type.csv",
    "overlay_connections": "kumu_overlay_connections_import_type.csv",
    "comention_elements": "kumu_comention_elements_import_type.csv",
    "comention_connections": "kumu_comention_connections_import_type (1).csv",
}

def _read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(RAW_DIR / RAW_FILES[name])

def load_raw():
    return {name: _read_csv(name) for name in RAW_FILES}

def attach_layer(df: pd.DataFrame, layer: str) -> pd.DataFrame:
    out = df.copy()
    out["layer"] = layer
    return out

def build_processed_tables(save: bool = True):
    raw = load_raw()

    nodes = pd.concat(
        [
            attach_layer(raw["core_elements"], "core"),
            attach_layer(raw["overlay_elements"], "overlay"),
            attach_layer(raw["comention_elements"], "comention"),
        ],
        ignore_index=True,
        sort=False,
    )

    edges = pd.concat(
        [
            attach_layer(raw["core_connections"], "core"),
            attach_layer(raw["overlay_connections"], "overlay"),
            attach_layer(raw["comention_connections"], "comention"),
        ],
        ignore_index=True,
        sort=False,
    )

    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        nodes.to_csv(PROCESSED_DIR / "nodes_all.csv", index=False)
        edges.to_csv(PROCESSED_DIR / "edges_all.csv", index=False)

    return nodes, edges
