# %%
"""Generate a two-panel figure for RL loop discovery characterization."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "requests.jsonl"
SUMMARY_PATH = ROOT / "results" / "loop_discovery_summary.csv"
OUT_DIR = ROOT / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERSONAL = "#3F72AF"
GROUP = "#112D4E"
LIGHT = "#DBE2EF"
GRID = "#B8C4D6"

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from paper_style import COLUMN_WIDTH, FONT_SIZE, apply_style, save_figure

apply_style()
# Compact side-by-side panels: larger than the original when printed at
# column width, while retaining approximately the original PDF aspect ratio.
plt.rcParams.update(
    {
        "font.size": 7.5,
        "axes.labelsize": 7.5,
        "axes.titlesize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 7.5,
    }
)


def _load_summary() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with SUMMARY_PATH.open() as f:
        for row in csv.DictReader(f):
            parsed: dict[str, Any] = dict(row)
            for key in [
                "request_rate",
                "expected_period_s",
                "median_loop_period_s",
                "mean_loop_period_s",
                "p25_loop_period_s",
                "p75_loop_period_s",
                "cv_loop_period",
                "iqr_over_median",
                "mae_after_1_loop_s",
                "mae_after_2_loops_s",
                "mae_after_3_loops_s",
                "mae_after_5_loops_s",
                "relative_mae_after_3_loops",
            ]:
                parsed[key] = float(parsed[key])
            for key in ["buffer_size", "n_sampling_requests", "n_training_requests"]:
                parsed[key] = int(parsed[key])
            rows.append(parsed)
    return rows


def _training_times_s(rows: list[dict[str, Any]]) -> list[float]:
    times = [r["monotonic_ns"] for r in rows if r.get("request_kind") == "training"]
    if not times:
        return []
    t0 = times[0]
    return [(t - t0) / 1e9 for t in times]


def _prediction_errors(times_s: list[float], warmup_intervals: int) -> list[float]:
    if len(times_s) < warmup_intervals + 2:
        return []
    intervals = [times_s[i] - times_s[i - 1] for i in range(1, len(times_s))]
    errors: list[float] = []
    for next_idx in range(warmup_intervals + 1, len(times_s)):
        observed_intervals = intervals[: next_idx - 1]
        if len(observed_intervals) < warmup_intervals:
            continue
        period_hat = median(observed_intervals)
        pred = times_s[next_idx - 1] + period_hat
        errors.append(abs(pred - times_s[next_idx]))
    return errors


def _tenant_group(tenant_id: str) -> str:
    return "Group" if tenant_id.endswith("-shared") else "Personal"


def _load_requests() -> dict[str, list[dict[str, Any]]]:
    by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with DATA_PATH.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            by_tenant[row["tenant_id"]].append(row)
    for rows in by_tenant.values():
        rows.sort(key=lambda r: r["monotonic_ns"])
    return dict(by_tenant)


def _convergence_series(
    by_tenant: dict[str, list[dict[str, Any]]],
) -> dict[str, list[float]]:
    warmups = [1, 2, 3, 4, 5, 6, 8]
    out: dict[str, list[float]] = {"Personal": [], "Group": []}
    for group in ["Personal", "Group"]:
        for w in warmups:
            rel_errors: list[float] = []
            for tenant_id, rows in by_tenant.items():
                if _tenant_group(tenant_id) != group:
                    continue
                times = _training_times_s(rows)
                if len(times) < w + 2:
                    continue
                intervals = [times[i] - times[i - 1] for i in range(1, len(times))]
                med_period = median(intervals)
                errs = _prediction_errors(times, w)
                if errs and med_period > 0:
                    rel_errors.append(100.0 * mean(errs) / med_period)
            out[group].append(mean(rel_errors) if rel_errors else 0.0)
    return out


def main() -> None:
    summaries = _load_summary()
    warmups = [1, 2, 3, 4, 5, 6, 8]
    if DATA_PATH.exists():
        conv = _convergence_series(_load_requests())
    else:
        recovered = json.loads(
            (ROOT / "results" / "convergence_recovered.json").read_text()
        )
        warmups, conv = recovered["warmups"], recovered["groups"]
        print("Using prediction-error points recovered from the original PDF.")

    rows = sorted(summaries, key=lambda s: s["median_loop_period_s"])
    labels = [r["tenant_id"].replace("-shared", "").replace("-A", "") for r in rows]
    y = list(range(len(rows)))
    med = [r["median_loop_period_s"] / 60.0 for r in rows]
    xerr_low = [
        max(0.0, r["median_loop_period_s"] - r["p25_loop_period_s"]) / 60.0
        for r in rows
    ]
    xerr_high = [
        max(0.0, r["p75_loop_period_s"] - r["median_loop_period_s"]) / 60.0
        for r in rows
    ]
    colors = [GROUP if r["group"] == "Group" else PERSONAL for r in rows]

    fig, (ax_period, ax_pred) = plt.subplots(
        1,
        2,
        figsize=(COLUMN_WIDTH, 1.62),
        gridspec_kw={"width_ratios": [1.45, 1.0]},
    )

    # Panel A: discovered periods.
    ax_period.barh(
        y,
        med,
        xerr=[xerr_low, xerr_high],
        color=colors,
        edgecolor="white",
        linewidth=0.5,
        height=0.62,
        error_kw={"elinewidth": 0.8, "ecolor": "#222222", "capsize": 0},
    )
    ax_period.set_yticks(y)
    ax_period.set_yticklabels(labels)
    ax_period.set_xlabel("Training-loop period (min)", labelpad=2)
    ax_period.set_xticks([0, 15, 30])
    ax_period.grid(axis="x", linestyle="--", linewidth=0.45, alpha=0.45, color=GRID)
    ax_period.spines["top"].set_visible(False)
    ax_period.spines["right"].set_visible(False)

    # Panel B: prediction convergence.
    ax_pred.plot(
        warmups,
        conv["Personal"],
        marker="o",
        linewidth=1.1,
        markersize=2.8,
        color=PERSONAL,
        label="Personal",
    )
    ax_pred.plot(
        warmups,
        conv["Group"],
        marker="o",
        linewidth=1.1,
        markersize=2.8,
        color=GROUP,
        label="Group",
    )
    ax_pred.set_xlabel("Observed intervals", labelpad=2)
    ax_pred.set_xticks([2, 4, 6, 8])
    ax_pred.set_yticks([0, 5, 10])
    ax_pred.set_ylabel("Prediction error (%)", labelpad=2)
    ax_pred.set_ylim(0, max(max(conv["Personal"]), max(conv["Group"])) * 1.25)
    ax_pred.grid(axis="y", linestyle="--", linewidth=0.45, alpha=0.45, color=GRID)
    ax_pred.spines["top"].set_visible(False)
    ax_pred.spines["right"].set_visible(False)

    legend_handles = [
        Line2D([0], [0], color=PERSONAL, lw=4, label="Personal"),
        Line2D([0], [0], color=GROUP, lw=4, label="Group"),
    ]
    ax_pred.legend(
        handles=legend_handles,
        frameon=False,
        loc="lower right",
        fontsize=6.5,
        handlelength=1.2,
        handletextpad=0.4,
        borderaxespad=0.4,
        labelspacing=0.4,
    )

    # ax_period.set_title("(a) Loop periods", loc="left", pad=3)
    # ax_pred.set_title("(b) Prediction error", loc="left", pad=3)
    fig.subplots_adjust(left=0.185, right=0.985, bottom=0.20, top=0.89, wspace=0.34)
    for ax in (ax_period, ax_pred):
        ax.tick_params(axis="both", pad=2, length=2.5)
    save_figure(fig, OUT_DIR, "rl_loop_discovery_two_panel", vertical_pad=0.022)


if __name__ == "__main__":
    main()

# %%
