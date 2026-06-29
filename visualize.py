"""
Visualization for AI Freedom Island simulation results.
Reads results/{world}/awi.json and crimes.json, produces a dashboard PNG.

Usage:
  python visualize.py                         # all worlds found in results/
  python visualize.py --worlds qwen_world gpt_world
  python visualize.py --output dashboard.png
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import numpy as np


# ── color palette — one color per world ──────────────────────────────────────

WORLD_COLORS = {
    "qwen_world":    "#E6A817",   # amber
    "gpt_world":     "#10A37F",   # openai green
    "gemini_world":  "#4285F4",   # google blue
    "claude_world":  "#CC785C",   # anthropic terracotta
    "mixed_world":   "#9B59B6",   # purple
    "deepseek_world":"#E74C3C",   # red
}
DEFAULT_COLORS = plt.cm.tab10.colors


def color_for(world: str, idx: int) -> str:
    return WORLD_COLORS.get(world, DEFAULT_COLORS[idx % len(DEFAULT_COLORS)])


WORLD_LABELS = {
    "qwen_world":    "Qwen",
    "gpt_world":     "GPT-4.1",
    "gemini_world":  "Gemini 2.5 Flash",
    "claude_world":  "Claude Sonnet 4.6",
    "mixed_world":   "Mixed",
    "deepseek_world":"DeepSeek-V3",
}


# ── data loading ──────────────────────────────────────────────────────────────

def load_world(world_dir: Path) -> dict | None:
    awi_path = world_dir / "awi.json"
    crime_path = world_dir / "crimes.json"
    if not awi_path.exists():
        return None
    awi = json.loads(awi_path.read_text(encoding="utf-8"))
    crimes = json.loads(crime_path.read_text(encoding="utf-8")) if crime_path.exists() else []
    return {"name": world_dir.name, "awi": awi, "crimes": crimes}


def load_all_worlds(results_dir: Path, filter_names: list[str] | None = None) -> list[dict]:
    worlds = []
    for d in sorted(results_dir.iterdir()):
        if not d.is_dir():
            continue
        if filter_names and d.name not in filter_names:
            continue
        data = load_world(d)
        if data and data["awi"]:
            worlds.append(data)
    return worlds


# ── per-day series helpers ────────────────────────────────────────────────────

def get_series(awi: list[dict], key: str) -> tuple[list[int], list[float]]:
    days = [s["day"] for s in awi]
    vals = [s.get(key, 0) for s in awi]
    return days, vals


def crimes_per_day(crimes: list[dict], max_day: int) -> tuple[list[int], list[int]]:
    counts: dict[int, int] = {d: 0 for d in range(1, max_day + 1)}
    for c in crimes:
        d = c.get("day", 1)
        if d in counts:
            counts[d] += 1
    days = sorted(counts.keys())
    return days, [counts[d] for d in days]


def cumulative_crimes(crimes: list[dict], max_day: int) -> tuple[list[int], list[int]]:
    days, daily = crimes_per_day(crimes, max_day)
    cumul = []
    total = 0
    for v in daily:
        total += v
        cumul.append(total)
    return days, cumul


# ── main dashboard ────────────────────────────────────────────────────────────

def plot_dashboard(worlds: list[dict], output_path: str = "dashboard.png"):
    if not worlds:
        print("No world data found.")
        return

    fig = plt.figure(figsize=(18, 14))
    fig.patch.set_facecolor("#0F1117")

    gs = gridspec.GridSpec(
        3, 3,
        figure=fig,
        hspace=0.45,
        wspace=0.35,
        left=0.07, right=0.97,
        top=0.91, bottom=0.07,
    )

    ax_pop    = fig.add_subplot(gs[0, 0])   # M1 population
    ax_crime  = fig.add_subplot(gs[0, 1])   # M2 cumulative crimes
    ax_daily  = fig.add_subplot(gs[0, 2])   # M2 crimes/day
    ax_space  = fig.add_subplot(gs[1, 0])   # M3 space exploration
    ax_gov    = fig.add_subplot(gs[1, 1])   # M5 governance approval rate
    ax_expr   = fig.add_subplot(gs[1, 2])   # M6 public expression
    ax_social = fig.add_subplot(gs[2, 0])   # M7 social fabric
    ax_econ   = fig.add_subplot(gs[2, 1])   # M8 gini coefficient
    ax_bar    = fig.add_subplot(gs[2, 2])   # final AWI bar chart

    AXES = [ax_pop, ax_crime, ax_daily, ax_space, ax_gov, ax_expr, ax_social, ax_econ, ax_bar]
    for ax in AXES:
        ax.set_facecolor("#1A1D27")
        ax.tick_params(colors="#AAAAAA", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333344")

    def style_ax(ax, title, ylabel="", xlabel="Day"):
        ax.set_title(title, color="#DDDDDD", fontsize=9, pad=6, fontweight="bold")
        ax.set_ylabel(ylabel, color="#888888", fontsize=7.5)
        ax.set_xlabel(xlabel, color="#888888", fontsize=7.5)
        ax.grid(color="#2A2D3A", linewidth=0.5, linestyle="--")

    legend_patches = []

    for idx, w in enumerate(worlds):
        name   = w["name"]
        label  = WORLD_LABELS.get(name, name)
        color  = color_for(name, idx)
        awi    = w["awi"]
        crimes = w["crimes"]
        max_day = awi[-1]["day"] if awi else 15

        legend_patches.append(mpatches.Patch(color=color, label=label))

        lw = 1.8

        # M1 — population
        days, vals = get_series(awi, "agents_alive")
        ax_pop.plot(days, vals, color=color, linewidth=lw, marker="o", markersize=2)

        # M2 — cumulative crimes
        cd, cv = cumulative_crimes(crimes, max_day)
        ax_crime.plot(cd, cv, color=color, linewidth=lw)

        # M2 — crimes per day
        dd, dv = crimes_per_day(crimes, max_day)
        ax_daily.plot(dd, dv, color=color, linewidth=lw, alpha=0.85)

        # M3 — space exploration
        days, vals = get_series(awi, "avg_locations_visited")
        ax_space.plot(days, vals, color=color, linewidth=lw)

        # M5 — governance approval rate
        days, vals = get_series(awi, "avg_vote_approval_rate")
        vals_pct = [v * 100 for v in vals]
        ax_gov.plot(days, vals_pct, color=color, linewidth=lw)

        # M6 — public expression (billboard + diary)
        days_b, bb = get_series(awi, "billboard_posts")
        days_d, dd2 = get_series(awi, "diary_entries")
        combined = [b + d for b, d in zip(bb, dd2)]
        ax_expr.plot(days_b, combined, color=color, linewidth=lw)

        # M7 — avg relationships
        days, vals = get_series(awi, "avg_relationships")
        ax_social.plot(days, vals, color=color, linewidth=lw)

        # M8 — gini
        days, vals = get_series(awi, "gini")
        ax_econ.plot(days, vals, color=color, linewidth=lw)

    # Reference lines
    ax_pop.axhline(10, color="#555566", linewidth=0.8, linestyle=":")
    ax_gov.axhline(70, color="#FF6B6B", linewidth=0.8, linestyle=":", label="70% required")

    style_ax(ax_pop,   "M1 — Population Health",        "Agents Alive")
    style_ax(ax_crime, "M2 — Cumulative Crimes",         "Total Crimes")
    style_ax(ax_daily, "M2 — Crimes per Day",            "Crimes")
    style_ax(ax_space, "M3 — Space Exploration",         "Avg Locations/Agent")
    style_ax(ax_gov,   "M5 — Governance Approval %",    "Approval Rate (%)")
    style_ax(ax_expr,  "M6 — Public Expression",        "Posts + Diary Entries")
    style_ax(ax_social,"M7 — Avg Relationships/Agent",  "Relationships")
    style_ax(ax_econ,  "M8 — Economic Inequality (Gini)","Gini Coefficient")

    # Final AWI bar chart — last snapshot comparison
    metrics = ["agents_alive", "total_crimes", "avg_locations_visited",
               "avg_tools_used", "billboard_posts", "avg_relationships", "gini"]
    metric_labels = ["M1 Alive", "M2 Crimes", "M3 Locations",
                     "M4 Tools", "M6 Posts", "M7 Relations", "M8 Gini"]

    x = np.arange(len(metrics))
    bar_width = 0.8 / max(len(worlds), 1)

    for idx, w in enumerate(worlds):
        awi = w["awi"]
        if not awi:
            continue
        final = awi[-1]
        color = color_for(w["name"], idx)
        offset = (idx - len(worlds) / 2 + 0.5) * bar_width
        vals = [final.get(m, 0) for m in metrics]
        # Normalize each metric to [0,1] relative to max across worlds for visual comparison
        bars = ax_bar.bar(x + offset, vals, width=bar_width * 0.9,
                          color=color, alpha=0.85, label=WORLD_LABELS.get(w["name"], w["name"]))

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(metric_labels, rotation=30, ha="right",
                           color="#AAAAAA", fontsize=7)
    style_ax(ax_bar, "Final Day AWI Comparison", "Value", xlabel="")

    # Global legend
    legend = fig.legend(
        handles=legend_patches,
        loc="upper center",
        ncol=min(len(worlds), 5),
        frameon=False,
        fontsize=9,
        bbox_to_anchor=(0.5, 0.97),
    )
    for text in legend.get_texts():
        text.set_color("#DDDDDD")

    fig.suptitle(
        "AI Freedom Island — Agent World Indicators",
        color="#FFFFFF", fontsize=14, fontweight="bold", y=0.995,
    )

    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Dashboard saved to: {output_path}")


# ── crime breakdown chart ─────────────────────────────────────────────────────

def plot_crime_breakdown(worlds: list[dict], output_path: str = "crimes.png"):
    if not worlds:
        return

    crime_types = ["theft", "arson", "assault", "intimidation"]
    n = len(worlds)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4), sharey=False)
    fig.patch.set_facecolor("#0F1117")
    if n == 1:
        axes = [axes]

    for idx, (w, ax) in enumerate(zip(worlds, axes)):
        ax.set_facecolor("#1A1D27")
        crimes = w["crimes"]
        counts = {t: 0 for t in crime_types}
        for c in crimes:
            t = c.get("type", "")
            if t in counts:
                counts[t] += 1

        vals = [counts[t] for t in crime_types]
        colors = ["#E74C3C", "#E67E22", "#9B59B6", "#3498DB"]
        bars = ax.bar(crime_types, vals, color=colors, alpha=0.85, width=0.6)
        ax.set_title(WORLD_LABELS.get(w["name"], w["name"]),
                     color="#DDDDDD", fontsize=10, fontweight="bold")
        ax.tick_params(colors="#AAAAAA", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#333344")
        ax.set_facecolor("#1A1D27")
        ax.grid(axis="y", color="#2A2D3A", linewidth=0.5, linestyle="--")

        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                        str(val), ha="center", va="bottom", color="#FFFFFF", fontsize=9)

    fig.suptitle("Crime Breakdown by World & Type",
                 color="#FFFFFF", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Crime breakdown saved to: {output_path}")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worlds", nargs="*", default=None,
                        help="World names to include (default: all in results/)")
    parser.add_argument("--output", default="results/dashboard.png")
    parser.add_argument("--crimes-output", default="results/crimes.png")
    args = parser.parse_args()

    results_dir = Path("results")
    worlds = load_all_worlds(results_dir, args.worlds)

    if not worlds:
        print("No completed worlds found in results/. Run experiments first.")
        return

    print(f"Loaded {len(worlds)} worlds: {[w['name'] for w in worlds]}")
    plot_dashboard(worlds, args.output)
    plot_crime_breakdown(worlds, args.crimes_output)


if __name__ == "__main__":
    main()
