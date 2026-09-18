"""Evaluation figures for the LoopWeave paper.

Each ``#%%`` cell renders one figure after the setup cell. The script collects
the evaluation data used for the accompanying figures.
"""

# %% Setup
from __future__ import annotations

from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.transforms import Bbox
from matplotlib.ticker import NullLocator

try:
    import pandas as pd
except ImportError:  # The GPU-utilization mock path works without pandas.
    pd = None

sysname = "LoopWeave"
baselines = ["Serial", "Unified", "Colocate", "Static-Disagg", sysname]
# Column-major order for a 3-column, 2-row legend:
# Serial / Static-Disagg, Unified / LoopWeave, and Colocate.
PANEL_LEGEND_ORDER = [0, 3, 1, 4, 2]
PANEL_LEGEND_LABELS = ["Serial", "Static-Disagg", "Unified", sysname, "Colocate"]

PALETTE = {
    "paper": "#F9F7F7",
    "mist": "#DBE2EF",
    "blue": "#3F72AF",
    "navy": "#112D4E",
    "steel": "#6096B4",
    "cyan": "#93BFCF",
    "pale": "#BDCDD6",
    "sand": "#EEE9DA",
    "loopweave": "#AA96DA",
}
SYSTEM_COLORS = {
    "Serial": PALETTE["pale"],
    "Unified": PALETTE["sand"],
    "Colocate": PALETTE["cyan"],
    "Static-Disagg": PALETTE["steel"],
    sysname: PALETTE["loopweave"],
}
SYSTEM_MARKERS = {
    "Serial": "o",
    "Unified": "s",
    "Colocate": "^",
    "Static-Disagg": "D",
    sysname: "*",
}
BASELINE_COLORS = [SYSTEM_COLORS[name] for name in baselines]

# Export at actual inclusion widths in the paper manuscript (no font scaling).
TEXT_WIDTH_IN = 7.0
COLUMN_WIDTH_IN = (TEXT_WIDTH_IN - 0.33) / 2
FULL_WIDTH = COLUMN_WIDTH_IN
HALF_WIDTH = 0.48 * COLUMN_WIDTH_IN
REFERENCE_WIDTH = 0.31 * TEXT_WIDTH_IN
# Shared evaluation-figure scale: labels, ticks, legends, and value labels
# intentionally use the same 9 pt size for a consistent final appearance.
LABEL_SIZE = TICK_SIZE = LEGEND_SIZE = ANNOTATION_SIZE = PANEL_LEGEND_SIZE = 9
COMPACT_LEGEND_SIZE = 5
STANDALONE_LEGEND_SIZE = LEGEND_SIZE
SLO_LEGEND_SIZE = 7
SLO_HEIGHT = 1.75
# Keep the axes in exactly the same position in all three SLO panels.  The
# response-time legend sits below the tick labels, rather than beside them.
SLO_LAYOUT = dict(left=0.28, right=0.985, bottom=0.35, top=0.965)


def slo_layout(fig: plt.Figure, *, legend: bool = False) -> None:
    """Identical axes position and canvas for the three side-by-side panels."""
    fig.subplots_adjust(**SLO_LAYOUT)
    if not legend:
        return
    handles = [
        Patch(facecolor=SYSTEM_COLORS[name], edgecolor="black", label=name)
        for name in baselines
    ]
    fig.legend(
        handles=handles,
        frameon=False,
        ncol=3,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.025),
        borderaxespad=0,
        borderpad=0,
        fontsize=7.5,
        handlelength=0.8,
        handleheight=0.7,
        columnspacing=0.6,
        handletextpad=0.25,
    )


ROOT_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT_DIR / "figures" / "exp_figure"
OUT_DIR.mkdir(parents=True, exist_ok=True)

mpl.rcParams.update(
    {
        # The manuscript's LaTeX style selects a Times-family typeface.
        "font.family": "Times New Roman",
        "text.usetex": False,
        "text.color": "black",
        "axes.labelcolor": "black",
        "xtick.color": "black",
        "ytick.color": "black",
        "font.size": LABEL_SIZE,
        "axes.labelsize": LABEL_SIZE,
        "axes.titlesize": LABEL_SIZE,
        "xtick.labelsize": TICK_SIZE,
        "ytick.labelsize": TICK_SIZE,
        "legend.fontsize": LEGEND_SIZE,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.01,
        "savefig.transparent": True,
        "axes.linewidth": 0.8,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3.2,
        "ytick.major.size": 3.2,
        "lines.linewidth": 1.35,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def style_axis(ax: plt.Axes, *, grid_axis: str | None = "y") -> None:
    # Leave the axes patch transparent so the PDF has no white rectangle when
    # it is placed on a colored or non-white LaTeX page.
    ax.set_facecolor("none")
    if grid_axis is not None:
        ax.grid(
            axis=grid_axis, linestyle="--", linewidth=0.45, alpha=0.35, color="black"
        )
    else:
        ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("black")
    ax.spines["bottom"].set_color("black")
    ax.tick_params(colors="black")
    ax.xaxis.label.set_color("black")
    ax.yaxis.label.set_color("black")


def save_figure(fig: plt.Figure, stem: str, *, slo: bool = False) -> None:
    """Trim vertical padding without changing the paper-calibrated width.

    SLO panels share the same canvas and axes; preserving their
    common bounds keeps the x axes aligned when the PDFs are placed in a row.
    Transparent exports remove the white background in both PDF and PNG.
    """
    fig.canvas.draw()
    if slo:
        # Identical, uncropped canvases preserve the horizontal x-axis level
        # when these three PDFs are arranged side by side.
        bounds = Bbox.from_bounds(0, 0, fig.get_figwidth(), fig.get_figheight())
    else:
        content = fig.get_tightbbox(fig.canvas.get_renderer())
        bounds = Bbox.from_extents(
            content.x0 - 0.02,
            content.y0 - 0.02,
            content.x1 + 0.02,
            content.y1 + 0.02,
        )
    for suffix in ("pdf", "png"):
        target = OUT_DIR / f"{stem}.{suffix}"
        try:
            fig.savefig(
                target,
                bbox_inches=bounds,
                pad_inches=0,
                transparent=True,
            )
        except OSError:
            # A PDF open in a desktop viewer may be locked on Windows. Preserve
            # the regenerated figure under an explicit alternate name instead
            # of preventing subsequent figures from being exported.
            alternate = OUT_DIR / f"{stem}_updated.{suffix}"
            fig.savefig(
                alternate,
                bbox_inches=bounds,
                pad_inches=0,
                transparent=True,
            )
            print(f"Could not overwrite {target}; wrote {alternate} instead.")
    print(OUT_DIR / f"{stem}.pdf")


def annotate_bars(
    ax: plt.Axes, bars, fmt: str = "{:.0f}", dy: float = 2.0, rotation: float = 0
) -> None:
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + dy,
            fmt.format(height),
            rotation=rotation,
            ha="center",
            va="bottom",
            fontsize=ANNOTATION_SIZE,
            color="black",
            zorder=5,
        )


# %% Throughput on Qwen3 models
# Unit: completed RL training steps per hour after warm-up on the 8-GPU setup.
model_groups = ["Qwen3-4B", "Qwen3-32B"]
throughput_by_model = {
    "Qwen3-4B": np.array([184.3, 39.9, 381.5, 283.9, 541.9]),
    "Qwen3-32B": np.array([116.3, 25.9, np.nan, 179.5, 342.1]),
}

fig, ax = plt.subplots(figsize=(FULL_WIDTH, 1.9))
group_x = np.arange(len(model_groups))
width = 0.13
offsets = (np.arange(len(baselines)) - (len(baselines) - 1) / 2) * width
for group_idx, model in enumerate(model_groups):
    for idx, name in enumerate(baselines):
        value = throughput_by_model[model][idx]
        x = group_x[group_idx] + offsets[idx]
        if np.isnan(value):
            ax.text(
                x,
                80,
                "OOM",
                rotation=90,
                ha="center",
                va="bottom",
                fontsize=7,
                color="black",
                zorder=5,
            )
            continue
        bars = ax.bar(
            x,
            value,
            width,
            label=name if group_idx == 0 else None,
            color=SYSTEM_COLORS[name],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
        # Show only the best and runner-up values in each model group.
        ranked = sorted(
            (v, i) for i, v in enumerate(throughput_by_model[model]) if not np.isnan(v)
        )
        if idx == ranked[-1][1]:
            annotate_bars(ax, bars, fmt="{:.0f}", dy=8.0, rotation=0)
        elif idx == ranked[-2][1]:
            annotate_bars(ax, bars, fmt="{:.0f}", dy=8.0)
ax.set_xticks(group_x)
ax.set_xticklabels(["Qwen3-4B", "Qwen3-32B"])
ax.set_ylabel("Training steps / hour")
ax.set_ylim(0, 700)
fig.legend(
    *ax.get_legend_handles_labels(),
    frameon=False,
    ncols=3,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.99),
    fontsize=STANDALONE_LEGEND_SIZE,
    handlelength=1.0,
    columnspacing=0.65,
    handletextpad=0.3,
)
style_axis(ax, grid_axis=None)
fig.subplots_adjust(left=0.23, right=0.985, bottom=0.22, top=0.70)
save_figure(fig, "eval_throughput_gpu_budget")


# %% Scaling with tenant counts
tenants = np.array([1, 2, 4, 8, 16])
# Unit: aggregate completed RL training steps/hour on Qwen3-4B.
scaling_throughput = {
    "Serial": np.array([156, 166, 186, 184, 183]),
    "Unified": np.array([12, 22, 30, 40, 42]),
    "Colocate": np.array([210, 305, 345, 381, 305]),
    "Static-Disagg": np.array([155, 228, 255, 284, 228]),
    sysname: np.array([303, 508, 523, 542, 414]),
}

fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2.05))
for idx, name in enumerate(baselines):
    ax.plot(
        tenants,
        scaling_throughput[name],
        marker=SYSTEM_MARKERS[name],
        markersize=5.5 if name == sysname else 3.8,
        markeredgecolor="black",
        markeredgewidth=0.7,
        color=SYSTEM_COLORS[name],
        linewidth=2.2 if name == sysname else 1.2,
        label=name,
    )
ax.axvline(8, color=PALETTE["loopweave"], linestyle="--", linewidth=1.0, alpha=0.75)
ax.annotate(
    "Peak",
    (8, scaling_throughput[sysname][3]),
    xytext=(3.5, 690),
    ha="center",
    fontsize=ANNOTATION_SIZE,
    arrowprops=dict(arrowstyle="-", color="black", lw=0.6),
)
ax.set_xscale("linear")
ax.set_xticks(tenants)
ax.set_xticklabels([str(t) for t in tenants])
ax.set_xlabel("Tenants", labelpad=6)
ax.set_ylabel("Training steps / hour")
ax.set_ylim(0, 800)
fig.legend(
    *ax.get_legend_handles_labels(),
    frameon=False,
    ncols=3,
    loc="upper center",
    bbox_to_anchor=(0.5, 0.99),
    fontsize=STANDALONE_LEGEND_SIZE,
    handlelength=1.0,
    columnspacing=0.65,
    handletextpad=0.3,
)
style_axis(ax)
fig.subplots_adjust(left=0.19, right=0.985, bottom=0.21, top=0.70)
save_figure(fig, "eval_scaling_tenants")


# %% Response time
# Unit: seconds. Measured SLO response times on Qwen3-4B.
response_time_slo = {
    "Training": np.array([146.7, 20.0, 25.8, 72.8, 29.6]),
    "Sampling": np.array([140.3, 703.2, 16.8, 16.1, 11.3]),
}

fig, ax = plt.subplots(figsize=(REFERENCE_WIDTH, SLO_HEIGHT))
group_x = np.arange(2)
width = 0.13
offsets = (np.arange(len(baselines)) - (len(baselines) - 1) / 2) * width
for group_idx, metric in enumerate(["Training", "Sampling"]):
    for idx, name in enumerate(baselines):
        x = group_x[group_idx] + offsets[idx]
        value = response_time_slo[metric][idx]
        ax.bar(
            x,
            value,
            width,
            label=name if group_idx == 0 else None,
            color=SYSTEM_COLORS[name],
            edgecolor="black",
            linewidth=0.8,
            zorder=3,
        )
ax.set_yscale("log")
ax.set_yticks([10, 30, 100, 300, 700])
ax.set_yticklabels(["10", "30", "100", "300", "700"])
ax.set_xticks(group_x)
ax.set_xticklabels(["Training", "Sampling"])
ax.set_ylabel("Response time (s)")
ax.set_ylim(5, 1000)
style_axis(ax)
slo_layout(fig, legend=True)
save_figure(fig, "eval_response_time", slo=True)


# %% Fidelity
# Absolute sequence-level log-probability bias for each system.
logprob_bias = np.array([0.1147, 0.0195, 0.1131, 0.1141, 0.0181])

fig, ax = plt.subplots(figsize=(REFERENCE_WIDTH, SLO_HEIGHT))
x = np.arange(len(baselines))
bars = ax.bar(
    x,
    logprob_bias,
    width=0.56,
    color=BASELINE_COLORS,
    edgecolor="black",
    linewidth=0.8,
    zorder=3,
)
for bar, value in zip(bars, logprob_bias):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.004,
        f"{value:.3f}",
        rotation=0,
        ha="center",
        va="bottom",
        fontsize=ANNOTATION_SIZE,
        color="black",
    )
ax.set_xticks(x)
ax.set_xticklabels(baselines, rotation=55, ha="right")
ax.tick_params(axis="x", labelsize=7)
ax.set_ylabel("Log-probability bias")
ax.set_ylim(0, 0.18)
ax.set_yticks([0, 0.05, 0.10, 0.15])
ax.set_yticklabels(["0.00", "0.05", "0.10", "0.15"])
style_axis(ax, grid_axis=None)
slo_layout(fig)
save_figure(fig, "eval_fidelity_mean_logprob_mismatch", slo=True)


# %% Freshness
# Average policy-version staleness observed across tenants.
average_staleness = np.array([2.19, 0.52, 1.84, 3.45, 2.58])

fig, ax = plt.subplots(figsize=(REFERENCE_WIDTH, SLO_HEIGHT))
x = np.arange(len(baselines))
bars = ax.bar(
    x,
    average_staleness,
    width=0.56,
    color=BASELINE_COLORS,
    edgecolor="black",
    linewidth=0.8,
    zorder=3,
)
for bar, value in zip(bars, average_staleness):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.08,
        f"{value:.2f}",
        ha="center",
        va="bottom",
        fontsize=ANNOTATION_SIZE,
        color="black",
    )
ax.set_xticks(x)
ax.set_xticklabels(baselines, rotation=55, ha="right")
ax.tick_params(axis="x", labelsize=7)
ax.set_ylabel("Mean staleness (versions)")
ax.set_ylim(0, 4.0)
style_axis(ax, grid_axis=None)
slo_layout(fig)
save_figure(fig, "eval_freshness", slo=True)


# %% Calibrator performance
# Accuracy of Static-Disagg and LoopWeave (existing experiment values). GSM8K is single-seed; MATH uses the
# multi-seed aggregate for GRPO and the strongest single seed for REINFORCE.
methods = ["REINFORCE", "GRPO"]
tasks = ["GSM8K", "MATH"]
accuracy_static_disagg = {
    "GSM8K": np.array([0.867, 0.933]),
    "MATH": np.array([0.600, 0.740]),
}
accuracy_loopweave = {
    "GSM8K": np.array([0.933, 0.967]),
    "MATH": np.array([0.860, 0.807]),
}

fig, ax = plt.subplots(figsize=(FULL_WIDTH, 1.9))
bar_width = 0.11
condition_gap = 0.13
method_gap = 0.50
method_centers = [-method_gap / 2, method_gap / 2]
condition_colors = [PALETTE["steel"], PALETTE["loopweave"]]
condition_labels = ["Static-Disagg", sysname]

for task_idx, task in enumerate(tasks):
    for method_idx, method in enumerate(methods):
        for condition_idx, condition in enumerate(condition_labels):
            values = (
                accuracy_static_disagg if condition_idx == 0 else accuracy_loopweave
            )
            value = values[task][method_idx]
            offset = method_centers[method_idx] + (condition_idx - 0.5) * condition_gap
            bar = ax.bar(
                task_idx + offset,
                value,
                bar_width,
                color=condition_colors[condition_idx],
                edgecolor="black",
                linewidth=0.7,
                hatch="" if condition_idx == 1 else "//",
                zorder=3,
            )
            ax.text(
                task_idx + offset,
                value + 0.012,
                f"{value:.2f}",
                rotation=0,
                ha="center",
                va="bottom",
                fontsize=ANNOTATION_SIZE,
                color="black",
            )

axis_transform = ax.get_xaxis_transform()
for task_idx, task in enumerate(tasks):
    for method_idx, method in enumerate(methods):
        center = task_idx + method_centers[method_idx]
        ax.text(
            center,
            -0.10,
            method,
            transform=axis_transform,
            ha="center",
            va="top",
            fontsize=LEGEND_SIZE,
            color="black",
        )
    ax.text(
        task_idx,
        -0.23,
        task,
        transform=axis_transform,
        ha="center",
        va="top",
        fontsize=TICK_SIZE,
        color="black",
        fontweight="normal",
    )

ax.set_xticks([])
ax.set_ylabel("Accuracy")
ax.set_ylim(0.5, 1.1)
ax.set_yticks([0.5, 0.6, 0.7, 0.8, 0.9, 1])
ax.set_yticklabels(["0.5", "0.6", "0.7", "0.8", "0.9", "1"])
ax.set_xlim(-0.45, len(tasks) - 0.55)

boundary = 0.5
ax.plot(
    [boundary, boundary],
    [-0.02, 1.02],
    transform=axis_transform,
    color="black",
    linestyle="-",
    linewidth=0.9,
    alpha=0.65,
    clip_on=False,
    zorder=4,
)
legend_handles = [
    Patch(
        facecolor=condition_colors[0],
        edgecolor="black",
        hatch="//",
        label="Static-Disagg",
    ),
    Patch(facecolor=condition_colors[1], edgecolor="black", label=sysname),
]
ax.legend(
    handles=legend_handles,
    frameon=False,
    ncol=2,
    loc="upper center",
    bbox_to_anchor=(0.5, 1.08),
    fontsize=LEGEND_SIZE,
)
style_axis(ax, grid_axis=None)
fig.tight_layout(pad=0.25)
save_figure(fig, "eval_calibrator_performance")


# %% Ablation Study, 8 GPUs, compare throughput and log-probability bias.
# Bias is absolute sequence-level log-probability bias.
ablation_baseline_points = {
    "Serial": (0.1141, 153.0),
    "Colocate": (0.1141, 381.5),
    "Unified": (0.0195, 39.9),
}
ablation_loopweave_points = [
    ("Static-Disagg", 0.1141, 186.6),
    ("+hybrid/calibrator", 0.0181, 225.4),
    ("+sampling", 0.0181, 246.3),
    ("+fast", 0.0181, 270.6),
    ("+slow", 0.0181, 423.5),
]

fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2))
ablation_baseline_styles = {
    "Serial": (SYSTEM_COLORS["Serial"], SYSTEM_MARKERS["Serial"]),
    "Colocate": (SYSTEM_COLORS["Colocate"], SYSTEM_MARKERS["Colocate"]),
    "Unified": (SYSTEM_COLORS["Unified"], SYSTEM_MARKERS["Unified"]),
}
baseline_label_offsets = {
    "Serial": (9, -14, "left"),
    "Colocate": (9, 6, "left"),
    "Unified": (-7, 7, "right"),
}
for name, (bias, throughput) in ablation_baseline_points.items():
    color, marker = ablation_baseline_styles[name]
    ax.scatter(
        bias,
        throughput,
        s=30,
        color=color,
        marker=marker,
        edgecolor="black",
        linewidth=0.8,
        label=name,
        zorder=3,
    )
    dx, dy, ha = baseline_label_offsets[name]
    ax.annotate(
        name,
        (bias, throughput),
        textcoords="offset points",
        xytext=(dx, dy),
        fontsize=LEGEND_SIZE,
        color="black",
        ha=ha,
    )

# Join the cumulative additions in their experimental order.
ax.plot(
    [point[1] for point in ablation_loopweave_points],
    [point[2] for point in ablation_loopweave_points],
    color=SYSTEM_COLORS[sysname],
    linewidth=1.6,
    linestyle="--",
    zorder=2,
)
for idx, (name, bias, throughput) in enumerate(ablation_loopweave_points):
    ax.scatter(
        bias,
        throughput,
        s=70 if idx == len(ablation_loopweave_points) - 1 else 30,
        color=SYSTEM_COLORS["Static-Disagg"] if idx == 0 else SYSTEM_COLORS[sysname],
        marker=SYSTEM_MARKERS["Static-Disagg"] if idx == 0 else SYSTEM_MARKERS[sysname],
        edgecolor="black",
        linewidth=0.8,
        label=None,
        zorder=4,
    )

loopweave_label_offsets = {
    "Static-Disagg": (9, 12, "left"),
    "+hybrid/calibrator": (-12, -15, "right"),
    "+sampling": (-12, -3, "right"),
    "+fast": (-32, 11, "right"),
    "+slow": (-32, -5, "right"),
}
for name, bias, throughput in ablation_loopweave_points:
    dx, dy, ha = loopweave_label_offsets[name]
    ax.annotate(
        name,
        (bias, throughput),
        linespacing=1.6,
        arrowprops=(
            dict(arrowstyle="-", color="black", lw=0.6, shrinkB=7)
            if name in {"+hybrid/calibrator", "+sampling", "+fast", "+slow"}
            else None
        ),
        textcoords="offset points",
        xytext=(dx, dy),
        fontsize=LEGEND_SIZE,
        color="black",
        ha=ha,
    )

final_bias, final_throughput = ablation_loopweave_points[-1][1:]
ax.annotate(
    f"{sysname} final",
    (final_bias, final_throughput),
    textcoords="offset points",
    xytext=(-12, 9),
    ha="right",
    va="bottom",
    fontsize=LEGEND_SIZE,
    color="black",
)

ax.set_xscale("log")
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xlim(0.18, 0.012)  # Reversed: larger bias sits closer to the origin.
ax.set_xticks([0.12, 0.05, 0.02])
ax.set_xticklabels(["0.12", "0.05", "0.02"])
ax.set_xlabel("Log-probability bias")
ax.set_ylabel("Training steps / hour")
ax.set_ylim(0, 500)
style_axis(ax, grid_axis=None)
fig.tight_layout(pad=0.25)
save_figure(fig, "eval_ablation_quality_throughput")

# %%
