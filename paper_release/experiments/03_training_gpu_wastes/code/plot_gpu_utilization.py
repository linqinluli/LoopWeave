"""
Plot GPU utilization over time for async and sync training experiments.
Generates publication-quality figures for the paper.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path

# ============================================================
# Scientific figure style configuration
# ============================================================
mpl.rcParams.update({








    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "xtick.major.size": 3.5,
    "ytick.major.size": 3.5,
    "lines.linewidth": 1.2,
    "axes.grid": True,
    "grid.linewidth": 0.4,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paper_style import COLUMN_WIDTH, FONT_SIZE, apply_style, save_figure
apply_style()

# Color palette (user-specified)
COLORS = {
    "training": "#F4D35E",  # warm yellow
    "sampling": "#457B9D",  # steel blue
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_async_data(filepath: Path) -> pd.DataFrame:
    """Load async GPU stats CSV (comma-separated, full datetime timestamps)."""
    df = pd.read_csv(filepath, skipinitialspace=True, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    df["timestamp"] = pd.to_datetime(df["timestamp"].str.strip())
    df["index"] = df["index"].astype(int)

    util_col = [c for c in df.columns if "utilization.gpu" in c][0]
    df["gpu_util"] = df[util_col].str.replace("%", "").str.strip().astype(float)

    t0 = df["timestamp"].min()
    df["elapsed_min"] = (df["timestamp"] - t0).dt.total_seconds() / 60.0

    return df[["elapsed_min", "index", "gpu_util"]].copy()


def load_sync_data(filepath: Path) -> pd.DataFrame:
    """Load sync GPU stats CSV (tab-separated, MM:SS.s timestamps)."""
    df = pd.read_csv(filepath, sep="\t", skipinitialspace=True, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    # Parse MM:SS.s timestamp -> minutes
    def parse_mmss(ts: str) -> float:
        ts = ts.strip()
        parts = ts.split(":")
        return int(parts[0]) + float(parts[1]) / 60.0

    df["raw_min"] = df["timestamp"].apply(parse_mmss)

    # Handle timestamp wrap-around (59:59 -> 00:00)
    # Track cumulative offset per GPU
    df["elapsed_min"] = np.nan
    for gpu_id in df["index"].unique():
        mask = df["index"] == gpu_id
        raw = df.loc[mask, "raw_min"].values
        offsets = np.zeros(len(raw))
        cumulative = 0.0
        for i in range(1, len(raw)):
            if raw[i] < raw[i - 1] - 30:  # significant drop = wrap
                cumulative += 60.0
            offsets[i] = cumulative
        df.loc[mask, "elapsed_min"] = raw + offsets

    # Shift to start from 0
    df["elapsed_min"] -= df["elapsed_min"].min()

    df["index"] = df["index"].astype(int)

    util_col = [c for c in df.columns if "utilization.gpu" in c][0]
    df["gpu_util"] = df[util_col].str.replace("%", "").str.strip().astype(float)

    return df[["elapsed_min", "index", "gpu_util"]].copy()


def smooth(y: np.ndarray, window: int = 60) -> np.ndarray:
    """Moving average smoothing."""
    if len(y) < window:
        return y
    kernel = np.ones(window) / window
    return np.convolve(y, kernel, mode="same")


def main():
    traces = {}
    raw_paths = [DATA_DIR / "gpu_stats_async.csv", DATA_DIR / "gpu_stats_sync.csv"]
    if all(path.exists() for path in raw_paths):
        for mode, frame in zip(("async", "sync"),
                               (load_async_data(raw_paths[0]), load_sync_data(raw_paths[1]))):
            for gpu in (0, 1):
                data = frame[frame["index"] == gpu].sort_values("elapsed_min")
                traces[mode, gpu] = (data["elapsed_min"].to_numpy(), smooth(data["gpu_util"].to_numpy()))
    else:
        # PDF vertices are already smoothed, not raw experiment samples.
        recovered = pd.read_csv(DATA_DIR / "gpu_utilization_recovered.csv")
        for (mode, gpu), data in recovered.groupby(["mode", "index"], sort=False):
            traces[mode, gpu] = (data["elapsed_min"].to_numpy(), data["gpu_util"].to_numpy())
        print("Using recovered displayed curves; no additional smoothing or raw-log statistics.")
    fig, axes = plt.subplots(2, 1, figsize=(COLUMN_WIDTH, 1.98))
    for ax, mode, title in zip(axes, ("async", "sync"),
                              ("(a) Asynchronous training", "(b) Synchronous training")):
        for gpu, role in ((0, "training"), (1, "sampling")):
            x, y = traces[mode, gpu]
            ax.plot(x, y, color=COLORS[role], label=role.capitalize(), alpha=0.95, linewidth=0.8)
        ax.set_ylabel("GPU util. (%)")
        if ax is axes[-1]:
            ax.set_xlabel("Elapsed time (min)")
        ax.set_ylim(-2, 105)
        ax.set_xlim(0, max(traces[mode, 0][0].max(), traces[mode, 1][0].max()) * 1.05)
        ax.set_yticks([0, 50, 100])
        ax.set_title(title, loc="left", pad=3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(loc="lower right", framealpha=0.9, edgecolor="none",
                  fontsize=7.0, handlelength=1.3, handletextpad=0.4,
                  borderpad=0.3, labelspacing=0.25)
    fig.tight_layout(pad=0.3, h_pad=0.65)
    save_figure(fig, OUT_DIR, "gpu_utilization_over_time", vertical_pad=0.022)
    plt.close(fig)


if __name__ == "__main__":
    main()
