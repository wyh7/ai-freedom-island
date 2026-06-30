"""
Milestone 2: Statistical Analysis Module
Aggregates results from multiple repeated runs to compute confidence intervals
and identify statistically significant behavioral differences across models.

Usage:
    python simulation/statistical_analysis.py --batch results/batch_milestone2_social_simulation.json
    python simulation/statistical_analysis.py --worlds m2_qwen_r1 m2_qwen_r2 m2_qwen_r3
"""

from __future__ import annotations
import json
import argparse
import math
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorldStats:
    """Statistics for a single completed world."""
    world_name: str
    model: str
    tags: list
    days: int
    alive: int
    crimes: int
    proposals: int
    gini: float
    billboard: int
    diary: int
    avg_relationships: float
    drift_score: Optional[float] = None
    tunnel_vision_events: int = 0
    sensing_ratio: Optional[float] = None


@dataclass
class GroupStats:
    """Aggregated statistics across multiple runs of same model."""
    model: str
    n: int
    # Mean ± std for key metrics
    crimes_mean: float = 0.0
    crimes_std: float = 0.0
    gini_mean: float = 0.0
    gini_std: float = 0.0
    alive_mean: float = 0.0
    alive_std: float = 0.0
    proposals_mean: float = 0.0
    proposals_std: float = 0.0
    drift_score_mean: float = 0.0
    drift_score_std: float = 0.0
    tunnel_vision_rate: float = 0.0  # fraction of runs with tunnel vision
    # 95% confidence interval (mean ± 1.96 * std/sqrt(n))
    crimes_ci95: tuple = field(default_factory=lambda: (0.0, 0.0))
    gini_ci95: tuple = field(default_factory=lambda: (0.0, 0.0))


def _mean(vals: list) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list) -> float:
    if len(vals) < 2:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _ci95(vals: list) -> tuple:
    if len(vals) < 2:
        m = _mean(vals)
        return (m, m)
    m = _mean(vals)
    s = _std(vals)
    margin = 1.96 * s / math.sqrt(len(vals))
    return (round(m - margin, 3), round(m + margin, 3))


def load_world_stats(world_name: str, results_dir: str = "results") -> Optional[WorldStats]:
    """Load AWI and audit data for a single world."""
    base = Path(results_dir) / world_name
    awi_path = base / "awi.json"
    if not awi_path.exists():
        return None

    awi = json.loads(awi_path.read_text(encoding="utf-8"))
    if not awi:
        return None
    last = awi[-1]

    # Load drift score if available
    drift_score = None
    drift_path = base / "drift_report.json"
    if drift_path.exists():
        dr = json.loads(drift_path.read_text(encoding="utf-8"))
        drift_score = dr.get("drift_score")

    # Load tunnel vision
    tunnel_events = 0
    threat_path = base / "threat_analysis.json"
    if threat_path.exists():
        ta = json.loads(threat_path.read_text(encoding="utf-8"))
        tunnel_events = ta.get("total_tunnel_windows", 0)

    # Load sensorium
    sensing_ratio = None
    sensor_path = base / "sensorium.json"
    if sensor_path.exists():
        sr = json.loads(sensor_path.read_text(encoding="utf-8"))
        sensing_ratio = sr.get("world_sensing_ratio")

    return WorldStats(
        world_name=world_name,
        model=world_name.split("_r")[0].replace("m2_", ""),  # e.g. "qwen"
        tags=[],
        days=last["day"],
        alive=last["agents_alive"],
        crimes=last["total_crimes"],
        proposals=last.get("total_proposals", 0),
        gini=last["gini"],
        billboard=last.get("billboard_posts", 0),
        diary=last.get("diary_entries", 0),
        avg_relationships=last.get("avg_relationships", 0.0),
        drift_score=drift_score,
        tunnel_vision_events=tunnel_events,
        sensing_ratio=sensing_ratio,
    )


def aggregate_group(worlds: list[WorldStats]) -> GroupStats:
    """Compute group statistics across repeated runs."""
    if not worlds:
        return GroupStats(model="unknown", n=0)

    crimes = [w.crimes for w in worlds]
    ginis = [w.gini for w in worlds]
    alives = [w.alive for w in worlds]
    proposals = [w.proposals for w in worlds]
    drift_scores = [w.drift_score for w in worlds if w.drift_score is not None]
    tunnel_runs = sum(1 for w in worlds if w.tunnel_vision_events > 0)

    return GroupStats(
        model=worlds[0].model,
        n=len(worlds),
        crimes_mean=round(_mean(crimes), 2),
        crimes_std=round(_std(crimes), 2),
        crimes_ci95=_ci95(crimes),
        gini_mean=round(_mean(ginis), 3),
        gini_std=round(_std(ginis), 3),
        gini_ci95=_ci95(ginis),
        alive_mean=round(_mean(alives), 2),
        alive_std=round(_std(alives), 2),
        proposals_mean=round(_mean(proposals), 2),
        proposals_std=round(_std(proposals), 2),
        drift_score_mean=round(_mean(drift_scores), 3) if drift_scores else 0.0,
        drift_score_std=round(_std(drift_scores), 3) if drift_scores else 0.0,
        tunnel_vision_rate=round(tunnel_runs / len(worlds), 2),
    )


def print_comparison_table(groups: dict[str, GroupStats]):
    """Print a statistical comparison table across models."""
    print(f"\n{'='*75}")
    print("STATISTICAL ANALYSIS — Cross-Model Comparison")
    print(f"{'='*75}")
    print(f"{'Model':18s} {'N':3s} {'Crimes':>12s} {'Gini':>12s} "
          f"{'Alive':>8s} {'Proposals':>10s} {'Drift':>8s} {'TunnelVis%':>11s}")
    print("-" * 75)

    for model, g in sorted(groups.items()):
        if g.n == 0:
            continue
        crimes_str = f"{g.crimes_mean:.1f}±{g.crimes_std:.1f}"
        gini_str = f"{g.gini_mean:.3f}±{g.gini_std:.3f}"
        print(f"{model:18s} {g.n:3d} {crimes_str:>12s} {gini_str:>12s} "
              f"{g.alive_mean:>8.1f} {g.proposals_mean:>10.1f} "
              f"{g.drift_score_mean:>8.3f} {g.tunnel_vision_rate*100:>10.0f}%")

    print()
    print("95% Confidence Intervals (Crimes):")
    for model, g in sorted(groups.items()):
        if g.n >= 2:
            print(f"  {model:18s}: [{g.crimes_ci95[0]:.1f}, {g.crimes_ci95[1]:.1f}]")

    print()
    print("95% Confidence Intervals (Gini):")
    for model, g in sorted(groups.items()):
        if g.n >= 2:
            print(f"  {model:18s}: [{g.gini_ci95[0]:.3f}, {g.gini_ci95[1]:.3f}]")


def analyze_batch(world_names: list[str], results_dir: str = "results") -> dict:
    """Load and analyze a set of worlds, grouped by model."""
    all_stats = []
    for name in world_names:
        s = load_world_stats(name, results_dir)
        if s:
            all_stats.append(s)
        else:
            print(f"  Warning: No data for {name}")

    # Group by model
    groups_raw: dict = defaultdict(list)
    for s in all_stats:
        groups_raw[s.model].append(s)

    groups: dict = {model: aggregate_group(worlds)
                    for model, worlds in groups_raw.items()}

    print_comparison_table(groups)

    # Save summary
    summary = {
        "worlds_analyzed": len(all_stats),
        "groups": {
            model: {
                "n": g.n,
                "crimes_mean": g.crimes_mean,
                "crimes_ci95": list(g.crimes_ci95),
                "gini_mean": g.gini_mean,
                "gini_ci95": list(g.gini_ci95),
                "drift_score_mean": g.drift_score_mean,
                "tunnel_vision_rate": g.tunnel_vision_rate,
            }
            for model, g in groups.items()
        }
    }

    out = Path(results_dir) / "statistical_comparison.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Statistical analysis across repeated runs")
    parser.add_argument("--worlds", nargs="+", default=None, help="List of world names")
    parser.add_argument("--batch", default=None, help="Batch summary JSON file")
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    if args.batch and Path(args.batch).exists():
        batch = json.loads(Path(args.batch).read_text(encoding="utf-8"))
        world_names = [r["world"] for r in batch.get("results", []) if r.get("success")]
    elif args.worlds:
        world_names = args.worlds
    else:
        # Default: find all m2_ worlds
        results = Path(args.results_dir)
        world_names = [d.name for d in sorted(results.iterdir())
                       if d.is_dir() and d.name.startswith("m2_")]

    if not world_names:
        print("No worlds found. Run batch_runner.py first.")
        return

    print(f"Analyzing {len(world_names)} worlds: {world_names}")
    analyze_batch(world_names, args.results_dir)


if __name__ == "__main__":
    main()
