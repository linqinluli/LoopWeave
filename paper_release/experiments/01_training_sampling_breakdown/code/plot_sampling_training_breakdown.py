"""Generate the sampling/training ratio characterization figure."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "results.json"
OUT_DIR = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERSONAL = "#3F72AF"
GROUP = "#112D4E"
AUX = "#DBE2EF"
LIGHT = "#F9F7F7"
TEXT = "#112D4E"

plt.rcParams.update(
    {


        "axes.linewidth": 0.8,
        "figure.dpi": 300,


    }
)

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paper_style import COLUMN_WIDTH, FONT_SIZE, apply_style, save_figure
apply_style()


def load_ratios() -> tuple[list[float], list[float]]:
    with DATA_PATH.open() as f:
        data = json.load(f)

    personal_ratios: list[float] = []
    group_ratios: list[float] = []
    for name, info in data["per_tenant"].items():
        ratio = info["total_sampling_seconds"] / info["total_training_seconds"]
        if name.endswith("-shared"):
            group_ratios.append(ratio)
        else:
            personal_ratios.append(ratio)
    return personal_ratios, group_ratios


def main() -> None:
    categories = ["Personal", "Group"]
    if DATA_PATH.exists():
        ratios = load_ratios()
        mins, maxs = [min(r) for r in ratios], [max(r) for r in ratios]
        means, medians = [mean(r) for r in ratios], [median(r) for r in ratios]
    else:
        summary = json.loads((ROOT / "data" / "ratio_summary_recovered.json").read_text())
        groups = [summary["groups"][name] for name in categories]
        mins, maxs = [g["min"] for g in groups], [g["max"] for g in groups]
        means, medians = [g["mean"] for g in groups], [g["median"] for g in groups]
        print("Using summary values recovered from original PDF geometry.")

    fig, ax = plt.subplots(figsize=(COLUMN_WIDTH, 1.48))

    y_pos = [0, 1]
    bar_height = 0.40
    colors = [PERSONAL, GROUP]

    for i, (mn, mx, avg, med, color) in enumerate(zip(mins, maxs, means, medians, colors)):
        ax.barh(
            i,
            mx - mn,
            left=mn,
            height=bar_height,
            color=color,
            alpha=0.35,
            edgecolor=color,
            linewidth=1.25,
            zorder=2,
        )
        ax.plot(
            avg,
            i,
            "D",
            color=color,
            markersize=6.5,
            zorder=4,
            markeredgecolor=LIGHT,
            markeredgewidth=0.6,
        )
        ax.plot(
            med,
            i,
            "o",
            color=color,
            markersize=7.0,
            zorder=5,
            markeredgecolor=LIGHT,
            markeredgewidth=0.6,
        )
        ax.plot([mn, mn], [i - bar_height / 3, i + bar_height / 3], color=color, linewidth=1.5, zorder=3)
        ax.plot([mx, mx], [i - bar_height / 3, i + bar_height / 3], color=color, linewidth=1.5, zorder=3)
        ax.text(mn - 0.35, i, f"{mn:.1f}", va="center", ha="right", fontsize=FONT_SIZE, color=TEXT)
        ax.text(mx + 0.35, i, f"{mx:.1f}", va="center", ha="left", fontsize=FONT_SIZE, color=TEXT)
        ax.text(avg, i + bar_height / 2 + 0.10, f"mean {avg:.1f}×", va="bottom", ha="center", fontsize=FONT_SIZE, color=TEXT)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=FONT_SIZE)
    ax.set_xlabel("Sampling Time / Training Time", fontsize=FONT_SIZE)
    ax.tick_params(axis="x", labelsize=FONT_SIZE, colors=TEXT)
    ax.tick_params(axis="y", length=0, colors=TEXT)
    ax.set_xlim(-1.5, 25.5)
    ax.set_ylim(-0.65, 1.95)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(TEXT)
    ax.spines["bottom"].set_color(TEXT)
    ax.axvline(x=1, color=AUX, linestyle="--", linewidth=0.8, alpha=0.9)
    ax.text(1.2, -0.55, "1:1", fontsize=FONT_SIZE, color=TEXT, ha="center")

    legend_elements = [
        Line2D([0], [0], marker="D", color="w", markerfacecolor="#666666", markeredgecolor=LIGHT, markersize=6.5, label="Mean"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#666666", markeredgecolor=LIGHT, markersize=7.0, label="Median"),
        Line2D([0], [0], color="#666666", linewidth=1.5, label="Min/Max"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        fontsize=FONT_SIZE,
        frameon=False,
        ncol=3,
        columnspacing=0.65,
        handletextpad=0.3,
        handlelength=1.1,
    )

    plt.tight_layout(pad=0.25)
    save_figure(fig, OUT_DIR, "sampling_training_ratio_range")


if __name__ == "__main__":
    main()
