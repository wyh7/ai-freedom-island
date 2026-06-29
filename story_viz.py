"""
Story-driven visualization for AI Freedom Island.
Produces a newspaper-style summary card that anyone can read.
"""

from __future__ import annotations
import json, re, os
from pathlib import Path
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# ── world metadata ────────────────────────────────────────────────────────────

WORLDS = [
    {"key": "claude_world",  "model": "Claude Sonnet 4.6",  "color": "#CC785C", "emoji": "🔵"},
    {"key": "qwen_world",    "model": "Qwen Plus",           "color": "#E6A817", "emoji": "🟡"},
    {"key": "gpt_world",     "model": "GPT-4.1",             "color": "#10A37F", "emoji": "🟢"},
    {"key": "gemini_world",  "model": "Gemini 2.5 Flash",    "color": "#4285F4", "emoji": "🔴"},
]

CRIME_COLORS = {
    "theft":        "#E74C3C",
    "arson":        "#E67E22",
    "assault":      "#9B59B6",
    "intimidation": "#3498DB",
}


def load(world_key: str) -> dict:
    base = Path("results") / world_key
    awi = json.loads((base / "awi.json").read_text(encoding="utf-8"))
    crimes_path = base / "crimes.json"
    crimes = json.loads(crimes_path.read_text(encoding="utf-8")) if crimes_path.exists() else []
    log_path = Path("logs") / f"{world_key}_stdout.txt"
    log = log_path.read_text(encoding="utf-8", errors="ignore") if log_path.exists() else ""
    return {"awi": awi, "crimes": crimes, "log": log}


def final(awi: list) -> dict:
    return awi[-1] if awi else {}


def crimes_per_day(crimes: list, max_day: int) -> list:
    counts = [0] * (max_day + 1)
    for c in crimes:
        d = c.get("day", 1)
        if 0 < d <= max_day:
            counts[d] += 1
    return counts[1:]


def get_quote(log: str, pattern: str, minlen: int = 60) -> str:
    hits = re.findall(pattern, log)
    for h in hits:
        if len(h) >= minlen:
            return h[:110] + ("..." if len(h) > 110 else "")
    return ""


# ── main ──────────────────────────────────────────────────────────────────────

def make_story_card(output: str = "results/story.png"):
    data = {}
    for w in WORLDS:
        try:
            data[w["key"]] = load(w["key"])
        except Exception as e:
            print(f"  Skipping {w['key']}: {e}")

    if not data:
        print("No data found.")
        return

    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor("#0A0C14")

    # ── title bar ────────────────────────────────────────────────────────────
    title_ax = fig.add_axes([0.0, 0.91, 1.0, 0.09])
    title_ax.set_facecolor("#0A0C14")
    title_ax.axis("off")
    title_ax.text(0.5, 0.72, "AI Freedom Island — Season 1 Report",
                  ha="center", va="center", fontsize=20, fontweight="bold",
                  color="#FFFFFF", transform=title_ax.transAxes)
    title_ax.text(0.5, 0.25, "Five worlds, four models, 15 days of autonomous agent society",
                  ha="center", va="center", fontsize=11, color="#888899",
                  transform=title_ax.transAxes)

    # ── layout: 4 world columns ───────────────────────────────────────────────
    n = len(WORLDS)
    col_w = 1.0 / n
    pad = 0.01

    for i, w in enumerate(WORLDS):
        key = w["key"]
        if key not in data:
            continue
        d = data[key]
        awi = d["awi"]
        crimes = d["crimes"]
        log = d["log"]
        f = final(awi)

        col_left = i * col_w + pad
        col_right = col_left + col_w - 2 * pad
        color = w["color"]

        # ── header card ───────────────────────────────────────────────────────
        hdr_ax = fig.add_axes([col_left, 0.81, col_w - 2*pad, 0.09])
        hdr_ax.set_facecolor(color)
        hdr_ax.axis("off")
        hdr_ax.text(0.5, 0.65, w["model"],
                    ha="center", va="center", fontsize=12, fontweight="bold",
                    color="#FFFFFF", transform=hdr_ax.transAxes)
        alive = f.get("agents_alive", "?")
        status = "全员存活" if alive == 10 else f"{alive}/10 存活"
        hdr_ax.text(0.5, 0.22, status,
                    ha="center", va="center", fontsize=9, color="#FFFFFF",
                    alpha=0.9, transform=hdr_ax.transAxes)

        # ── stats row ─────────────────────────────────────────────────────────
        stats_ax = fig.add_axes([col_left, 0.70, col_w - 2*pad, 0.10])
        stats_ax.set_facecolor("#12151F")
        stats_ax.axis("off")

        total_crimes = f.get("total_crimes", 0)
        gini = f.get("gini", 0)
        proposals = f.get("total_proposals", 0)
        approval = f.get("avg_vote_approval_rate", 0) * 100
        bb = f.get("billboard_posts", 0)

        stats = [
            ("犯罪总数", str(total_crimes), "#FF6B6B" if total_crimes > 10 else "#88DD88"),
            ("经济不平等", f"{gini:.3f}", "#FF9B4A" if gini > 0.2 else "#88DD88"),
            ("治理提案", str(proposals), "#88BBFF"),
            ("支持率", f"{approval:.0f}%", "#FFD700" if approval > 85 else "#AAAAAA"),
            ("公告发帖", str(bb), "#AAAAFF"),
        ]

        for j, (label, val, vcolor) in enumerate(stats):
            x = 0.1 + j * 0.19
            stats_ax.text(x, 0.75, val, ha="center", va="center",
                          fontsize=13, fontweight="bold", color=vcolor,
                          transform=stats_ax.transAxes)
            stats_ax.text(x, 0.25, label, ha="center", va="center",
                          fontsize=7, color="#888899",
                          transform=stats_ax.transAxes)

        # ── crime timeline ────────────────────────────────────────────────────
        crime_ax = fig.add_axes([col_left, 0.52, col_w - 2*pad, 0.17])
        crime_ax.set_facecolor("#12151F")
        crime_ax.tick_params(colors="#666677", labelsize=7)
        for spine in crime_ax.spines.values():
            spine.set_edgecolor("#222233")

        days = list(range(1, 16))
        cpd = crimes_per_day(crimes, 15)
        if len(cpd) < 15:
            cpd += [0] * (15 - len(cpd))

        # stacked bar by crime type
        type_order = ["theft", "arson", "assault", "intimidation"]
        bottoms = [0] * 15
        for ctype in type_order:
            vals = [0] * 15
            for c in crimes:
                d_idx = c.get("day", 1) - 1
                if 0 <= d_idx < 15 and c.get("type") == ctype:
                    vals[d_idx] += 1
            crime_ax.bar(days, vals, bottom=bottoms, color=CRIME_COLORS[ctype],
                         width=0.75, alpha=0.85, label=ctype)
            bottoms = [b + v for b, v in zip(bottoms, vals)]

        crime_ax.set_xlim(0.5, 15.5)
        crime_ax.set_xlabel("Day", color="#666677", fontsize=7)
        crime_ax.set_ylabel("Crimes", color="#666677", fontsize=7)
        crime_ax.set_title("犯罪时间线", color="#CCCCDD", fontsize=8, pad=4)
        crime_ax.grid(axis="y", color="#1E2030", linewidth=0.5)

        if i == 0 and any(bottoms):
            patches = [mpatches.Patch(color=CRIME_COLORS[t], label=t) for t in type_order]
            crime_ax.legend(handles=patches, fontsize=6, frameon=False,
                            labelcolor="#AAAAAA", loc="upper right")

        # ── top criminals ─────────────────────────────────────────────────────
        crim_ax = fig.add_axes([col_left, 0.39, col_w - 2*pad, 0.12])
        crim_ax.set_facecolor("#12151F")
        crim_ax.axis("off")
        crim_ax.set_title("累计犯罪者排名", color="#CCCCDD", fontsize=8, pad=4)

        by_actor = Counter(c["actor"] for c in crimes)
        top3 = by_actor.most_common(3)
        if top3:
            names = [t[0] for t in top3]
            counts = [t[1] for t in top3]
            y_pos = [0.72, 0.45, 0.18]
            for rank, (name, cnt, yp) in enumerate(zip(names, counts, y_pos)):
                medal = ["🥇", "🥈", "🥉"][rank]
                crim_ax.text(0.05, yp, f"{medal} {name}", ha="left", va="center",
                             fontsize=8.5, color="#DDDDDD",
                             transform=crim_ax.transAxes)
                crim_ax.text(0.85, yp, str(cnt), ha="right", va="center",
                             fontsize=8.5, color="#FF6B6B", fontweight="bold",
                             transform=crim_ax.transAxes)
        else:
            crim_ax.text(0.5, 0.5, "无犯罪记录 ✓", ha="center", va="center",
                         fontsize=10, color="#88DD88",
                         transform=crim_ax.transAxes)

        # ── population line ────────────────────────────────────────────────────
        pop_ax = fig.add_axes([col_left, 0.23, col_w - 2*pad, 0.15])
        pop_ax.set_facecolor("#12151F")
        pop_ax.tick_params(colors="#666677", labelsize=7)
        for spine in pop_ax.spines.values():
            spine.set_edgecolor("#222233")

        pop_days = [s["day"] for s in awi]
        pop_vals = [s.get("agents_alive", 10) for s in awi]
        pop_ax.fill_between(pop_days, pop_vals, alpha=0.25, color=color)
        pop_ax.plot(pop_days, pop_vals, color=color, linewidth=2)
        pop_ax.axhline(10, color="#444455", linewidth=0.8, linestyle=":")
        pop_ax.set_ylim(0, 11)
        pop_ax.set_xlim(1, 15)
        pop_ax.set_ylabel("存活人数", color="#666677", fontsize=7)
        pop_ax.set_xlabel("Day", color="#666677", fontsize=7)
        pop_ax.set_title("种群存活曲线", color="#CCCCDD", fontsize=8, pad=4)
        pop_ax.grid(color="#1E2030", linewidth=0.5, linestyle="--")

        # ── quote box ─────────────────────────────────────────────────────────
        quote_ax = fig.add_axes([col_left, 0.04, col_w - 2*pad, 0.18])
        quote_ax.set_facecolor("#0E1020")
        quote_ax.axis("off")
        for spine in quote_ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(1.5)

        # pull a notable billboard post
        q = get_quote(log, r"post_to_billboard\((?:content|message)='([^']{60,}?)'")
        if not q:
            q = get_quote(log, r"write_diary\(content='([^']{60,}?)'")
        if not q:
            if total_crimes == 0:
                q = "秩序井然，无犯罪记录。治理机制运转正常。"
            else:
                first = crimes[0] if crimes else {}
                q = f"Day {first.get('day','?')}: {first.get('actor','?')} 首次实施{first.get('type','crime')}。"

        quote_ax.text(0.5, 0.88, "📋 典型事件",
                      ha="center", va="top", fontsize=7.5, color=color,
                      transform=quote_ax.transAxes, fontweight="bold")
        quote_ax.text(0.5, 0.68, f'"{q}"',
                      ha="center", va="top", fontsize=7.5, color="#CCCCDD",
                      transform=quote_ax.transAxes, wrap=True,
                      multialignment="center",
                      bbox=dict(boxstyle="round,pad=0.3", fc="#0A0C1A", ec="none"))

        # one-line verdict
        if total_crimes == 0:
            verdict = "🏛️ 零犯罪乌托邦 — 秩序完美，但是否有真实自由？"
        elif total_crimes < 5:
            verdict = f"⚠️ 低烈度社会 — 偶发犯罪，社会基本稳定"
        elif total_crimes < 30:
            verdict = f"🔥 中度动荡 — {total_crimes}起犯罪，{10 - alive}人死亡"
        else:
            verdict = f"💥 高度混乱 — {total_crimes}起犯罪，社会接近崩溃边缘"

        quote_ax.text(0.5, 0.12, verdict,
                      ha="center", va="bottom", fontsize=8, color="#FFFFFF",
                      transform=quote_ax.transAxes, fontweight="bold",
                      bbox=dict(boxstyle="round,pad=0.4", fc=color, alpha=0.3, ec="none"))

    # ── bottom legend for crime types ─────────────────────────────────────────
    leg_ax = fig.add_axes([0.0, 0.0, 1.0, 0.04])
    leg_ax.set_facecolor("#0A0C14")
    leg_ax.axis("off")
    patches = [mpatches.Patch(color=v, label=k) for k, v in CRIME_COLORS.items()]
    leg = leg_ax.legend(handles=patches, loc="center", ncol=4, frameon=False,
                        fontsize=9, bbox_to_anchor=(0.5, 0.5))
    for text in leg.get_texts():
        text.set_color("#AAAAAA")

    plt.savefig(output, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"Story card saved to: {output}")


if __name__ == "__main__":
    make_story_card()
