"""
Generate a world map image for AI Freedom Island.
Outputs: docs/world/WORLD_MAP.png
"""

from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

matplotlib.rcParams["font.family"] = ["Microsoft YaHei", "DejaVu Sans", "sans-serif"]
matplotlib.rcParams["axes.unicode_minus"] = False

LANDMARKS = {
    # key: (x, z, display_name, category, has_gated_tools)
    "home":              (0,    30,   "Home",              "residential", True),
    "town_hall":         (60,   60,   "Town Hall",         "municipal",   True),
    "police_station":    (60,  -60,   "Police Station",    "municipal",   True),
    "public_library":    (-60,  60,   "Public Library",    "municipal",   True),
    "bean_brew":         (-30,   0,   "Bean & Brew",       "commercial",  True),
    "agent_techhub":     (30,  -30,   "Agent TechHub",     "commercial",  True),
    "victory_arch":      (0,   -60,   "Victory Arch",      "commercial",  True),
    "fresh_mart":        (-60, -60,   "Fresh Mart",        "commercial",  False),
    "business_tower":    (60,    0,   "Business Tower",    "commercial",  False),
    "central_park":      (0,    30,   "Central Park",      "recreation",  False),
    "central_plaza":     (0,     0,   "Central Plaza",     "recreation",  True),
    "riverside_park":    (-90,  30,   "Riverside Park",    "recreation",  False),
    "gamestop_arena":    (30,  -90,   "GameStop Arena",    "entertainment", False),
    "sky_wheel":         (-30, -90,   "Sky Wheel",         "entertainment", False),
    "sunset_pier":       (30, -120,   "Sunset Pier",       "entertainment", False),
    "billboard":         (30,   30,   "Billboard",         "public",      True),
    "founders_memorial": (0,  -120,   "Founders Memorial", "public",      False),
}

# Separate home and central_park (same coords for clarity)
LANDMARKS["home"] = (-15, 45, "Home\n(per agent)", "residential", True)

CATEGORY_COLORS = {
    "residential":  "#E8C99A",
    "municipal":    "#7EB8D4",
    "commercial":   "#95D07F",
    "recreation":   "#B8A4D4",
    "entertainment":"#F4A460",
    "public":       "#F0C040",
}

CATEGORY_LABELS = {
    "residential":  "Residential",
    "municipal":    "Municipal",
    "commercial":   "Commercial",
    "recreation":   "Recreation",
    "entertainment":"Entertainment",
    "public":       "Public",
}


def draw_map(output_path: str = "docs/world/WORLD_MAP.png"):
    fig, ax = plt.subplots(1, 1, figsize=(14, 12))
    fig.patch.set_facecolor("#0D1117")
    ax.set_facecolor("#161B22")

    # Grid
    ax.grid(color="#21262D", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_xlim(-120, 90)
    ax.set_ylim(-145, 90)
    ax.set_aspect("equal")

    # Axes labels
    ax.set_xlabel("West ← X → East", color="#8B949E", fontsize=9)
    ax.set_ylabel("South ← Z → North", color="#8B949E", fontsize=9)
    ax.tick_params(colors="#8B949E", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363D")

    # Draw landmarks
    drawn_cats = set()
    for key, (x, z, name, cat, has_tools) in LANDMARKS.items():
        color = CATEGORY_COLORS[cat]
        alpha = 0.92

        # Box size
        w, h = 28, 14
        rect = FancyBboxPatch(
            (x - w/2, z - h/2), w, h,
            boxstyle="round,pad=1.5",
            facecolor=color, edgecolor="white" if has_tools else "#555",
            linewidth=1.8 if has_tools else 0.8, alpha=alpha, zorder=3
        )
        ax.add_patch(rect)

        # Name text
        fontsize = 6.5
        ax.text(x, z + 1, name, ha="center", va="center",
                fontsize=fontsize, color="#0D1117", fontweight="bold",
                zorder=4, multialignment="center")

        # Gated tool indicator
        if has_tools:
            ax.text(x, z - 5, "🔧", ha="center", va="center",
                    fontsize=5, zorder=4)

        drawn_cats.add(cat)

    # Title
    ax.set_title("AI Freedom Island — World Map", color="white",
                 fontsize=14, fontweight="bold", pad=12)

    # Legend
    legend_patches = []
    for cat, color in CATEGORY_COLORS.items():
        if cat in drawn_cats:
            legend_patches.append(
                mpatches.Patch(facecolor=color, edgecolor="white",
                               label=CATEGORY_LABELS[cat], linewidth=0.8)
            )
    # Add gated tools indicator
    legend_patches.append(
        mpatches.Patch(facecolor="none", edgecolor="white",
                       label="🔧 Has gated tools", linewidth=1.8)
    )

    leg = ax.legend(
        handles=legend_patches,
        loc="lower left",
        framealpha=0.85,
        facecolor="#161B22",
        edgecolor="#30363D",
        fontsize=8,
        ncol=2,
    )
    for t in leg.get_texts():
        t.set_color("white")

    # Compass rose
    ax.annotate("N", xy=(80, 80), fontsize=12, color="white",
                fontweight="bold", ha="center", va="center")
    ax.annotate("", xy=(80, 85), xytext=(80, 75),
                arrowprops=dict(arrowstyle="->", color="white", lw=1.5))

    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"World map saved to: {output_path}")


if __name__ == "__main__":
    draw_map()
