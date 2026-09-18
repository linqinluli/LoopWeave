#%%
"""Recreate the mismatch-severity plot from the released PDF.

The original per-round logs are unavailable. The values below were recovered
from the nine plotted points in the released figure, so this script is fully
self-contained and does not depend on a data file.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Reconstructed from the released figure (rounds 1--9).
ROUNDS = list(range(1, 10))
SERIES = {
    "Tinker": [0.0127, 0.0138, 0.0137, 0.0113, 0.0112, 0.0131, 0.0126, 0.0136, 0.0114],
    "Self-hosted": [0.0117, 0.0118, 0.0100, 0.0105, 0.0110, 0.0095, 0.0092, 0.0101, 0.0112],
    "Self-hosted (Quantized)": [0.0304, 0.0305, 0.0271, 0.0277, 0.0260, 0.0305, 0.0209, 0.0238, 0.0242],
}

LINE_COLORS = {
    "Tinker": "#D7E1F1",
    "Self-hosted": "#3F72AF",
    "Self-hosted (Quantized)": "#112D4E",
}
MARKERS = {"Tinker": "o", "Self-hosted": "s", "Self-hosted (Quantized)": "D"}

# Match the Times-family typeface selected by the paper's LaTeX style
# (mathptmx/pslatex). This is the balanced single-column reference scale.
plt.rcParams.update(
    {
        "font.family": "Times New Roman",
        "font.size": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        # Keep the legend at the same size as tick labels.
        "legend.fontsize": 7,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "text.color": "black",
        "axes.labelcolor": "black",
        "xtick.color": "black",
        "ytick.color": "black",
    }
)


def plot() -> None:
    # Single-column width, with a deliberately compact vertical footprint.
    fig, ax = plt.subplots(figsize=(3.35, 1.35))

    for name, values in SERIES.items():
        ax.plot(
            ROUNDS,
            values,
            label=name,
            color=LINE_COLORS[name],
            marker=MARKERS[name],
            markersize=4.5,
            markeredgecolor="black",
            markeredgewidth=0.55,
            linewidth=1.8,
            zorder=3,
        )

    ax.set_xlabel("RL Fine-tuning Round")
    ax.set_ylabel("Mean |Δ logprob|")
    ax.set_xlim(0.6, 9.4)
    ax.set_ylim(0.0082, 0.0317)
    ax.set_xticks(ROUNDS)
    ax.set_yticks([0.010, 0.015, 0.020, 0.025, 0.030])
    ax.grid(axis="y", linestyle="--", linewidth=0.5, color="#D7E1F1", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(direction="out", length=3.5, width=0.8, colors="black")

    legend = ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.05),
        ncol=3,
        frameon=False,
        handlelength=1.35,
        handletextpad=0.45,
        columnspacing=0.75,
        borderaxespad=0,
    )
    for text in legend.get_texts():
        text.set_color("black")

    fig.savefig(OUT_DIR / "mismatch_severity_comparison.pdf", bbox_inches="tight", pad_inches=0.01)
    fig.savefig(OUT_DIR / "mismatch_severity_comparison.png", dpi=300, bbox_inches="tight", pad_inches=0.01)


if __name__ == "__main__":
    plot()
