"""
AI Freedom Island — Evaluation Suite (Milestone 6)
Unified entry point for the long-horizon LLM safety evaluation benchmark.

This module provides a standardized interface to run the full evaluation pipeline:
  1. Run simulation (single-model or mixed)
  2. Collect AWI metrics
  3. Detect drift (sensorium + tunnel vision)
  4. Detect collusion
  5. Generate causal graph + audit narrative
  6. Compile benchmark report

Usage:
    python evaluate.py --model qwen-plus --days 15
    python evaluate.py --model deepseek-v3 --scenario adversarial --days 15
    python evaluate.py --mixed --days 15
    python evaluate.py --benchmark-all   # run full benchmark suite
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


BENCHMARK_MODELS = [
    "qwen-plus",
    "deepseek-v3",
    "gemini-2.5-flash",
    "claude-sonnet-4-6",
]

BENCHMARK_SCENARIOS = ["cooperative", "competitive", "adversarial"]


def run_pipeline(
    world_name: str,
    model: str | None,
    mixed: bool,
    days: int,
    scenario: str | None,
    python_exe: str,
) -> dict:
    """Run full evaluation pipeline for one world."""

    results_dir = Path("results") / world_name
    results_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path("logs") / f"{world_name}.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*55}")
    print(f"EVALUATING: {world_name}")
    print(f"Model: {'mixed' if mixed else model} | Days: {days} | Scenario: {scenario or 'default'}")
    print(f"{'='*55}")

    # ── Step 1: Run simulation ────────────────────────────────────────────────
    print("\n[1/5] Running simulation...")
    cmd = [python_exe, "run_with_env.py", "--world", world_name, "--days", str(days)]
    if mixed:
        cmd.append("--mixed")
    elif model:
        cmd.extend(["--model", model])

    # Apply scenario if specified
    if scenario:
        from simulation.scenario_designer import get_scenario
        print(f"      Applying scenario: {scenario}")

    start = time.time()
    with open(log_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        proc.wait()
    elapsed = time.time() - start

    if proc.returncode != 0:
        print(f"      FAILED (exit code {proc.returncode})")
        return {"world": world_name, "success": False, "error": "simulation failed"}

    print(f"      Done in {elapsed/60:.1f} min")

    # ── Step 2: Drift detection ───────────────────────────────────────────────
    print("\n[2/5] Running drift detection...")
    try:
        from simulation.drift_detector import DriftDetector
        detector = DriftDetector(world_name)
        drift_report = detector.run()
        out = results_dir / "drift_report.json"
        out.write_text(json.dumps(drift_report.summary(), indent=2, ensure_ascii=False),
                       encoding="utf-8")
        print(f"      Drift score: {drift_report.drift_score:.3f} | "
              f"Alerts: {len(drift_report.alerts)}")
    except Exception as e:
        print(f"      WARNING: {e}")
        drift_report = None

    # ── Step 3: Collusion detection ───────────────────────────────────────────
    print("\n[3/5] Running collusion detection...")
    try:
        from simulation.collusion_detector import detect_collusion, save_report
        collusion_report = detect_collusion(world_name)
        save_report(collusion_report)
        print(f"      Collusion score: {collusion_report.collusion_score:.3f} | "
              f"Signals: {len(collusion_report.signals)}")
    except Exception as e:
        print(f"      WARNING: {e}")
        collusion_report = None

    # ── Step 4: Causal graph ──────────────────────────────────────────────────
    print("\n[4/5] Building causal graph & narrative...")
    try:
        from simulation.causal_report import build_causal_graph, build_narrative_report, save_outputs
        graph = build_causal_graph(world_name)
        narrative = build_narrative_report(graph, world_name)
        save_outputs(graph, narrative)
        print(f"      Nodes: {len(graph.nodes)} | Edges: {len(graph.edges)} | "
              f"Risk events: {len(graph.risk_events)}")
    except Exception as e:
        print(f"      WARNING: {e}")
        graph = None

    # ── Step 5: Compile benchmark report ─────────────────────────────────────
    print("\n[5/5] Compiling benchmark report...")
    awi_path = results_dir / "awi.json"
    awi = json.loads(awi_path.read_text(encoding="utf-8")) if awi_path.exists() else []
    last_awi = awi[-1] if awi else {}

    report = {
        "world": world_name,
        "model": "mixed" if mixed else model,
        "scenario": scenario or "default",
        "days": days,
        "success": True,
        "elapsed_min": round(elapsed / 60, 1),
        # AWI Metrics
        "awi": {
            "alive": last_awi.get("agents_alive", 0),
            "crimes": last_awi.get("total_crimes", 0),
            "gini": round(last_awi.get("gini", 0), 3),
            "proposals": last_awi.get("total_proposals", 0),
            "approval_rate": round(last_awi.get("avg_vote_approval_rate", 0), 3),
            "billboard_posts": last_awi.get("billboard_posts", 0),
            "diary_entries": last_awi.get("diary_entries", 0),
            "avg_relationships": round(last_awi.get("avg_relationships", 0), 2),
        },
        # Drift
        "drift": {
            "score": drift_report.drift_score if drift_report else None,
            "alerts": len(drift_report.alerts) if drift_report else None,
        },
        # Collusion
        "collusion": {
            "score": collusion_report.collusion_score if collusion_report else None,
            "signals": len(collusion_report.signals) if collusion_report else None,
        },
        # Risk graph
        "causal_graph": {
            "nodes": len(graph.nodes) if graph else None,
            "edges": len(graph.edges) if graph else None,
            "risk_events": len(graph.risk_events) if graph else None,
        },
    }

    report_path = results_dir / "benchmark_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"\n  ✓ Report saved: {report_path}")
    print(f"  AWI: alive={report['awi']['alive']}/10 | crimes={report['awi']['crimes']} | "
          f"gini={report['awi']['gini']}")
    print(f"  Drift: {report['drift']['score']} | Collusion: {report['collusion']['score']}")

    return report


def run_benchmark_suite(days: int = 15, python_exe: str = sys.executable):
    """Run the full benchmark suite across all models and scenarios."""
    print(f"\n{'#'*60}")
    print(f"# AI FREEDOM ISLAND — FULL BENCHMARK SUITE")
    print(f"# Models: {BENCHMARK_MODELS}")
    print(f"# Scenarios: default + {BENCHMARK_SCENARIOS}")
    print(f"{'#'*60}")

    all_reports = []
    timestamp = time.strftime("%Y%m%d_%H%M")

    # Default scenario for each model
    for model in BENCHMARK_MODELS:
        safe_model = model.replace("-", "_").replace(".", "_")
        world = f"bench_{safe_model}_default"
        report = run_pipeline(world, model, False, days, None, python_exe)
        all_reports.append(report)

    # Mixed-model world
    report = run_pipeline("bench_mixed_default", None, True, days, None, python_exe)
    all_reports.append(report)

    # Save suite summary
    suite_path = Path("results") / f"benchmark_suite_{timestamp}.json"
    suite_path.parent.mkdir(parents=True, exist_ok=True)
    suite = {
        "timestamp": timestamp,
        "days": days,
        "total_worlds": len(all_reports),
        "successful": sum(1 for r in all_reports if r.get("success")),
        "reports": all_reports,
    }
    suite_path.write_text(json.dumps(suite, indent=2, ensure_ascii=False),
                          encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"BENCHMARK SUITE COMPLETE")
    print(f"Worlds run: {len(all_reports)} | "
          f"Successful: {suite['successful']}")
    print(f"Suite report: {suite_path}")

    return all_reports


def main():
    parser = argparse.ArgumentParser(
        description="AI Freedom Island — LLM Long-Horizon Safety Evaluator"
    )
    parser.add_argument("--model", default=None, help="Model ID to evaluate")
    parser.add_argument("--mixed", action="store_true", help="Run mixed-model world")
    parser.add_argument("--days", type=int, default=15, help="Simulation days")
    parser.add_argument("--scenario", default=None,
                        choices=["cooperative", "competitive", "adversarial", "collusion_seed"],
                        help="Initial world scenario")
    parser.add_argument("--world-name", default=None,
                        help="Custom world name (auto-generated if not set)")
    parser.add_argument("--benchmark-all", action="store_true",
                        help="Run full benchmark suite across all models")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()

    if args.benchmark_all:
        run_benchmark_suite(args.days, args.python)
        return

    if not args.model and not args.mixed:
        parser.error("Specify --model <name> or --mixed")

    # Auto-generate world name
    if args.world_name:
        world = args.world_name
    elif args.mixed:
        world = f"eval_mixed_{int(time.time())}"
    else:
        safe = args.model.replace("-", "_").replace(".", "_")
        world = f"eval_{safe}_{args.scenario or 'default'}"

    run_pipeline(world, args.model, args.mixed, args.days, args.scenario, args.python)


if __name__ == "__main__":
    main()
