"""
Generate all figures for the technical report.
Outputs: figures/fig_*.pdf (vector, for LaTeX inclusion)
"""

from __future__ import annotations
import json, os
from pathlib import Path
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["figure.dpi"] = 150

WORLDS = [
    {"key": "claude_world",  "label": "Claude Sonnet 4.6", "color": "#CC785C", "marker": "o"},
    {"key": "qwen_world",    "label": "Qwen Plus",          "color": "#E6A817", "marker": "s"},
    {"key": "gpt_world",     "label": "GPT-4.1",            "color": "#10A37F", "marker": "^"},
    {"key": "gemini_world",  "label": "Gemini 2.5 Flash",   "color": "#4285F4", "marker": "D"},
]

CRIME_COLORS = {
    "theft":        "#E74C3C",
    "arson":        "#E67E22",
    "assault":      "#9B59B6",
    "intimidation": "#3498DB",
}

FIG_DIR = Path("figures")
FIG_DIR.mkdir(exist_ok=True)

BG   = "#0F1117"
CARD = "#1A1D27"
TEXT = "#DDDDDD"
GRID = "#2A2D3A"


def load():
    data = {}
    for w in WORLDS:
        key = w["key"]
        awi = json.loads((Path("results") / key / "awi.json").read_text(encoding="utf-8"))
        cp  = Path("results") / key / "crimes.json"
        crimes = json.loads(cp.read_text(encoding="utf-8")) if cp.exists() else []
        data[key] = {"awi": awi, "crimes": crimes, "meta": w}
    return data


def style(ax, title="", xlabel="Day", ylabel=""):
    ax.set_facecolor(CARD)
    ax.set_title(title, color=TEXT, fontsize=10, fontweight="bold", pad=6)
    ax.set_xlabel(xlabel, color="#888899", fontsize=8)
    ax.set_ylabel(ylabel, color="#888899", fontsize=8)
    ax.tick_params(colors="#888899", labelsize=8)
    ax.grid(color=GRID, linewidth=0.6, linestyle="--", alpha=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333344")


def legend(ax, ncol=1, loc="best"):
    leg = ax.legend(ncol=ncol, framealpha=0.15, fontsize=7.5,
                    facecolor="#0F1117", edgecolor="#333344", loc=loc)
    for t in leg.get_texts():
        t.set_color(TEXT)


# ─────────────────────────────────────────────────────────────────────────────
# Fig 1: AWI Overview — 3x3 subplots, one line per world
# ─────────────────────────────────────────────────────────────────────────────

def fig_awi_overview(data):
    fig = plt.figure(figsize=(15, 10), facecolor=BG)
    gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35,
                            left=0.07, right=0.97, top=0.92, bottom=0.06)
    axes = [fig.add_subplot(gs[r, c]) for r in range(3) for c in range(3)]

    metrics = [
        ("agents_alive",            "M1 — Population Health",       "Agents Alive"),
        ("total_crimes",            "M2 — Cumulative Crimes",        "Total Crimes"),
        ("avg_locations_visited",   "M3 — Space Exploration",        "Avg Locations/Agent"),
        ("avg_tools_used",          "M4 — Tool Exploration",         "Avg Tools/Agent"),
        ("avg_vote_approval_rate",  "M5 — Governance Approval",      "Approval Rate"),
        ("billboard_posts",         "M6 — Billboard Posts",          "Posts"),
        ("diary_entries",           "M6 — Diary Entries",            "Entries"),
        ("avg_relationships",       "M7 — Social Fabric",            "Avg Relations/Agent"),
        ("gini",                    "M8 — Economic Inequality (Gini)","Gini Coefficient"),
    ]

    for ax, (key, title, ylabel) in zip(axes, metrics):
        style(ax, title, ylabel=ylabel)
        for w in WORLDS:
            awi = data[w["key"]]["awi"]
            days = [s["day"] for s in awi]
            vals = [s.get(key, 0) for s in awi]
            if key == "avg_vote_approval_rate":
                vals = [v * 100 for v in vals]
            ax.plot(days, vals, color=w["color"], linewidth=1.8,
                    marker=w["marker"], markersize=3, label=w["label"])

        if key == "agents_alive":
            ax.axhline(10, color="#555566", linewidth=0.8, linestyle=":")
            ax.set_ylim(0, 11)
        if key == "avg_vote_approval_rate":
            ax.axhline(70, color="#FF6B6B", linewidth=0.8, linestyle=":", alpha=0.6)

    legend(axes[0], ncol=2)
    fig.suptitle("Agent World Indicators (AWI) — 15-Day Comparison",
                 color="white", fontsize=13, fontweight="bold")
    fig.savefig(FIG_DIR / "fig_awi_overview.png", bbox_inches="tight", facecolor=BG, dpi=150)
    plt.close()
    print("Saved fig_awi_overview")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2: Crime Analysis — stacked bar per world + cumulative line
# ─────────────────────────────────────────────────────────────────────────────

def fig_crimes(data):
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), facecolor=BG)
    axes = axes.flatten()

    for ax, w in zip(axes, WORLDS):
        key    = w["key"]
        crimes = data[key]["crimes"]
        style(ax, f"{w['label']}", ylabel="Crimes/Day")
        ax.set_xlabel("Simulation Day")

        type_order = ["theft", "arson", "assault", "intimidation"]
        bottoms = [0] * 15
        days    = list(range(1, 16))

        for ctype in type_order:
            vals = [0] * 15
            for c in crimes:
                d = c.get("day", 1) - 1
                if 0 <= d < 15 and c.get("type") == ctype:
                    vals[d] += 1
            ax.bar(days, vals, bottom=bottoms, color=CRIME_COLORS[ctype],
                   width=0.7, alpha=0.85, label=ctype)
            bottoms = [b + v for b, v in zip(bottoms, vals)]

        total = sum(bottoms)
        ax.text(0.97, 0.96, f"Total: {total}", transform=ax.transAxes,
                ha="right", va="top", color=TEXT, fontsize=9, fontweight="bold")
        ax.set_xlim(0.5, 15.5)
        if total == 0:
            ax.text(7.5, 0.5, "Zero Crimes", ha="center", va="center",
                    fontsize=14, color="#88DD88", alpha=0.5,
                    transform=ax.transData)

        legend(ax, ncol=2)

    fig.suptitle("Crime Breakdown by World and Type", color="white",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(FIG_DIR / "fig_crimes.png", bbox_inches="tight", facecolor=BG, dpi=150)
    plt.close()
    print("Saved fig_crimes")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3: Final AWI Bar Chart — radar / grouped bar comparison
# ─────────────────────────────────────────────────────────────────────────────

def fig_final_comparison(data):
    import numpy as np
    fig, (ax_bar, ax_pop) = plt.subplots(1, 2, figsize=(14, 5), facecolor=BG)

    # Left: grouped bar of 6 normalized metrics
    metrics = [
        ("total_crimes",          "Crimes",     False),
        ("agents_alive",          "Alive/10",   False),
        ("total_proposals",       "Proposals",  False),
        ("avg_relationships",     "Relations",  False),
        ("gini",                  "Gini×10",    False),
        ("billboard_posts",       "BB Posts/10",False),
    ]

    x     = np.arange(len(metrics))
    width = 0.18
    style(ax_bar, "Final Day — Key Metrics Comparison", xlabel="", ylabel="Value")

    for i, w in enumerate(WORLDS):
        last  = data[w["key"]]["awi"][-1]
        vals  = []
        for mk, label, norm in metrics:
            v = last.get(mk, 0)
            if mk == "gini":
                v *= 10
            elif mk == "billboard_posts":
                v /= 10
            vals.append(v)
        offset = (i - 1.5) * width
        ax_bar.bar(x + offset, vals, width=width, color=w["color"],
                   alpha=0.85, label=w["label"])

    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels([m[1] for m in metrics], rotation=15, ha="right",
                            color="#AAAAAA", fontsize=8)
    legend(ax_bar, ncol=2)

    # Right: population survival curves
    style(ax_pop, "Population Survival (M1)", ylabel="Agents Alive")
    for w in WORLDS:
        awi  = data[w["key"]]["awi"]
        days = [s["day"] for s in awi]
        vals = [s.get("agents_alive", 10) for s in awi]
        ax_pop.fill_between(days, vals, alpha=0.12, color=w["color"])
        ax_pop.plot(days, vals, color=w["color"], linewidth=2.2,
                    marker=w["marker"], markersize=4, label=w["label"])
    ax_pop.axhline(10, color="#444455", linewidth=0.8, linestyle=":")
    ax_pop.set_ylim(0, 11)
    ax_pop.set_xlim(1, 15)
    legend(ax_pop)

    fig.suptitle("Cross-World Final Comparison", color="white",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG_DIR / "fig_final_comparison.png", bbox_inches="tight", facecolor=BG, dpi=150)
    plt.close()
    print("Saved fig_final_comparison")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4: Governance & Economy
# ─────────────────────────────────────────────────────────────────────────────

def fig_governance_economy(data):
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), facecolor=BG)

    # (a) Governance approval rate over time
    style(axes[0], "M5 — Governance Approval Rate (%)", ylabel="Approval (%)")
    for w in WORLDS:
        awi  = data[w["key"]]["awi"]
        days = [s["day"] for s in awi]
        vals = [s.get("avg_vote_approval_rate", 0) * 100 for s in awi]
        axes[0].plot(days, vals, color=w["color"], linewidth=2,
                     marker=w["marker"], markersize=4, label=w["label"])
    axes[0].axhline(70, color="#FF6B6B", linewidth=1, linestyle=":",
                    label="70% Required")
    axes[0].set_ylim(0, 105)
    legend(axes[0], ncol=2)

    # (b) Cumulative proposals over time
    style(axes[1], "M9 — Cumulative Governance Proposals", ylabel="Proposals")
    for w in WORLDS:
        awi  = data[w["key"]]["awi"]
        days = [s["day"] for s in awi]
        vals = [s.get("total_proposals", 0) for s in awi]
        axes[1].plot(days, vals, color=w["color"], linewidth=2,
                     marker=w["marker"], markersize=4, label=w["label"])
    legend(axes[1])

    # (c) Gini coefficient trajectory
    style(axes[2], "M8 — Economic Inequality (Gini)", ylabel="Gini Coefficient")
    for w in WORLDS:
        awi  = data[w["key"]]["awi"]
        days = [s["day"] for s in awi]
        vals = [s.get("gini", 0) for s in awi]
        axes[2].fill_between(days, vals, alpha=0.1, color=w["color"])
        axes[2].plot(days, vals, color=w["color"], linewidth=2,
                     marker=w["marker"], markersize=4, label=w["label"])
    axes[2].axhline(0.3, color="#FF9B4A", linewidth=0.8, linestyle=":",
                    label="High Inequality (0.3)")
    legend(axes[2])

    fig.suptitle("Governance and Economy Indicators", color="white",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "fig_governance_economy.png", bbox_inches="tight", facecolor=BG, dpi=150)
    plt.close()
    print("Saved fig_governance_economy")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5: Top criminals per world
# ─────────────────────────────────────────────────────────────────────────────

def fig_criminals(data):
    import numpy as np
    agents = ["Anchor","Anvil","Blackbox","Flora","Genome","Horizon","Kade","Lovely","Mira","Spark"]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4), facecolor=BG)

    for ax, w in zip(axes, WORLDS):
        crimes = data[w["key"]]["crimes"]
        by_actor = Counter(c["actor"] for c in crimes)
        vals = [by_actor.get(a, 0) for a in agents]
        colors_bar = [w["color"] if v > 0 else "#333344" for v in vals]
        y_pos = np.arange(len(agents))
        ax.barh(y_pos, vals, color=colors_bar, alpha=0.85)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(agents, color=TEXT, fontsize=8)
        style(ax, w["label"], xlabel="Crimes Committed", ylabel="")
        total = sum(vals)
        ax.text(0.97, 0.02, f"Total: {total}", transform=ax.transAxes,
                ha="right", va="bottom", color=TEXT, fontsize=9, fontweight="bold")
        if total == 0:
            ax.text(0.5, 0.5, "Zero Crimes", transform=ax.transAxes,
                    ha="center", va="center", fontsize=11, color="#88DD88", alpha=0.6)

    fig.suptitle("Crimes Committed per Agent per World",
                 color="white", fontsize=13, fontweight="bold")
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / "fig_criminals.png", bbox_inches="tight", facecolor=BG, dpi=150)
    plt.close()
    print("Saved fig_criminals")


if __name__ == "__main__":
    d = load()
    fig_awi_overview(d)
    fig_crimes(d)
    fig_final_comparison(d)
    fig_governance_economy(d)
    fig_criminals(d)
    print("\nAll figures saved to figures/")
