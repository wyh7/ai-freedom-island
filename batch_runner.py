"""
Milestone 2: Batch Experiment Manager
Manages multiple runs of the same or different configurations to enable
statistical analysis of emergent risks across heterogeneous agent populations.

Usage:
    python batch_runner.py --config config/batch_m2.yaml
    python batch_runner.py --quick-test
"""

from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ExperimentConfig:
    world_name: str
    model: Optional[str] = None          # single-model world
    mixed: bool = False                  # heterogeneous world
    days: int = 15
    starting_credits: float = 3.0       # lower = more survival pressure
    repeat: int = 1                      # number of repeat runs
    tags: list = field(default_factory=list)  # for grouping in analysis


@dataclass
class BatchConfig:
    name: str
    description: str
    experiments: list  # list[ExperimentConfig]
    output_dir: str = "results"
    analyze_after: bool = True  # run drift_detector after each run


MILESTONE2_BATCH = BatchConfig(
    name="milestone2_social_simulation",
    description=(
        "Milestone 2: Multi-batch world construction with heterogeneous agents. "
        "Observes emergent risks across cooperative, competitive, and mixed topologies."
    ),
    experiments=[
        # ── Batch A: Repeat runs for statistical confidence ──────────────────
        ExperimentConfig("m2_qwen_r1",     model="qwen-plus",      days=15, repeat=1, tags=["repeat", "qwen"]),
        ExperimentConfig("m2_qwen_r2",     model="qwen-plus",      days=15, repeat=1, tags=["repeat", "qwen"]),
        ExperimentConfig("m2_qwen_r3",     model="qwen-plus",      days=15, repeat=1, tags=["repeat", "qwen"]),
        ExperimentConfig("m2_deepseek_r1", model="deepseek-v3",    days=15, repeat=1, tags=["repeat", "deepseek"]),
        ExperimentConfig("m2_deepseek_r2", model="deepseek-v3",    days=15, repeat=1, tags=["repeat", "deepseek"]),
        ExperimentConfig("m2_deepseek_r3", model="deepseek-v3",    days=15, repeat=1, tags=["repeat", "deepseek"]),

        # ── Batch B: Heterogeneous mixed-model worlds ────────────────────────
        ExperimentConfig("m2_mixed_v1",    mixed=True, days=15, tags=["heterogeneous", "mixed"]),
        ExperimentConfig("m2_mixed_v2",    mixed=True, days=15, tags=["heterogeneous", "mixed"]),

        # ── Batch C: High-pressure survival scenarios ────────────────────────
        # (starting_credits=1 forces agents to compete for resources on Day 1)
        ExperimentConfig("m2_pressure_v1", model="qwen-plus",   days=15,
                         starting_credits=1.0, tags=["pressure", "high_stress"]),
        ExperimentConfig("m2_pressure_v2", model="deepseek-v3", days=15,
                         starting_credits=1.0, tags=["pressure", "high_stress"]),
    ]
)


def load_batch_config(path: str) -> BatchConfig:
    """Load batch config from YAML file."""
    import yaml
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    experiments = [ExperimentConfig(**e) for e in data.get("experiments", [])]
    return BatchConfig(
        name=data["name"],
        description=data.get("description", ""),
        experiments=experiments,
        output_dir=data.get("output_dir", "results"),
        analyze_after=data.get("analyze_after", True),
    )


def patch_starting_credits(credits: float):
    """Temporarily patch models.py to use custom starting credits."""
    models_path = Path("simulation/models.py")
    text = models_path.read_text(encoding="utf-8")
    import re
    patched = re.sub(
        r"credits: float = [\d.]+",
        f"credits: float = {credits}",
        text
    )
    models_path.write_text(patched, encoding="utf-8")


def run_experiment(exp: ExperimentConfig, python_exe: str = sys.executable) -> dict:
    """Run a single experiment and return timing/status info."""
    # Patch starting credits if needed
    patch_starting_credits(exp.starting_credits)

    cmd = [python_exe, "run_with_env.py", "--world", exp.world_name, "--days", str(exp.days)]
    if exp.mixed:
        cmd.append("--mixed")
    elif exp.model:
        cmd.extend(["--model", exp.model])

    log_path = Path("logs") / f"{exp.world_name}.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    start = time.time()
    print(f"\n  Starting: {exp.world_name} ({'mixed' if exp.mixed else exp.model}) "
          f"| {exp.days} days | CC_start={exp.starting_credits}")

    with open(log_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
        proc.wait()

    elapsed = time.time() - start
    success = proc.returncode == 0

    # Check AWI output
    awi_path = Path("results") / exp.world_name / "awi.json"
    awi_summary = {}
    if awi_path.exists():
        data = json.loads(awi_path.read_text(encoding="utf-8"))
        if data:
            last = data[-1]
            awi_summary = {
                "days": last["day"],
                "alive": last["agents_alive"],
                "crimes": last["total_crimes"],
                "gini": round(last["gini"], 3),
                "proposals": last.get("total_proposals", 0),
            }

    return {
        "world": exp.world_name,
        "model": exp.model or "mixed",
        "tags": exp.tags,
        "success": success,
        "elapsed_min": round(elapsed / 60, 1),
        "awi": awi_summary,
    }


def run_drift_analysis(world_name: str, python_exe: str = sys.executable):
    """Run drift detector on completed experiment."""
    cmd = [python_exe, "-m", "simulation.drift_detector", "--world", world_name, "--save"]
    subprocess.run(cmd, capture_output=True)


def run_batch(batch: BatchConfig, python_exe: str = sys.executable,
              parallel: bool = False) -> list:
    """Run all experiments in a batch (sequential or parallel)."""
    print(f"\n{'='*65}")
    print(f"BATCH: {batch.name}")
    print(f"DESC:  {batch.description}")
    print(f"RUNS:  {len(batch.experiments)}")
    print(f"{'='*65}")

    results = []

    if not parallel:
        for i, exp in enumerate(batch.experiments):
            print(f"\n[{i+1}/{len(batch.experiments)}]", end="")
            result = run_experiment(exp, python_exe)
            results.append(result)
            print(f"  → {'✓' if result['success'] else '✗'} "
                  f"{result['elapsed_min']}min | {result['awi']}")

            if batch.analyze_after and result["success"]:
                run_drift_analysis(exp.world_name, python_exe)
    else:
        # Parallel: launch all, then wait
        procs = []
        for exp in batch.experiments:
            patch_starting_credits(exp.starting_credits)
            cmd = [python_exe, "run_with_env.py", "--world", exp.world_name,
                   "--days", str(exp.days)]
            if exp.mixed:
                cmd.append("--mixed")
            elif exp.model:
                cmd.extend(["--model", exp.model])
            log = open(Path("logs") / f"{exp.world_name}.txt", "w", encoding="utf-8")
            proc = subprocess.Popen(cmd, stdout=log, stderr=log)
            procs.append((exp, proc, log, time.time()))
            print(f"  Launched: {exp.world_name} PID={proc.pid}")

        print(f"\n  Waiting for {len(procs)} processes...")
        for exp, proc, log, start in procs:
            proc.wait()
            log.close()
            elapsed = (time.time() - start) / 60
            awi_path = Path("results") / exp.world_name / "awi.json"
            awi = {}
            if awi_path.exists():
                d = json.loads(awi_path.read_text(encoding="utf-8"))
                if d:
                    last = d[-1]
                    awi = {"alive": last["agents_alive"], "crimes": last["total_crimes"],
                           "gini": round(last["gini"], 3)}
            result = {"world": exp.world_name, "model": exp.model or "mixed",
                      "tags": exp.tags, "success": proc.returncode == 0,
                      "elapsed_min": round(elapsed, 1), "awi": awi}
            results.append(result)
            print(f"  Done: {exp.world_name} → {awi}")

    # Save batch summary
    summary_path = Path("results") / f"batch_{batch.name}.json"
    summary = {
        "batch": batch.name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M"),
        "total": len(results),
        "success": sum(1 for r in results if r["success"]),
        "results": results,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False),
                             encoding="utf-8")
    print(f"\n  Batch summary saved: {summary_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Batch experiment runner")
    parser.add_argument("--config", default=None, help="YAML batch config file")
    parser.add_argument("--quick-test", action="store_true",
                        help="Run 2 experiments for 3 days as a smoke test")
    parser.add_argument("--parallel", action="store_true",
                        help="Run experiments in parallel")
    parser.add_argument("--python", default=sys.executable,
                        help="Python executable to use")
    args = parser.parse_args()

    if args.quick_test:
        batch = BatchConfig(
            name="quick_test",
            description="2-experiment smoke test (3 days each)",
            experiments=[
                ExperimentConfig("test_qwen",     model="qwen-turbo",  days=3, tags=["test"]),
                ExperimentConfig("test_deepseek", model="deepseek-v3", days=3, tags=["test"]),
            ]
        )
    elif args.config:
        batch = load_batch_config(args.config)
    else:
        batch = MILESTONE2_BATCH

    results = run_batch(batch, python_exe=args.python, parallel=args.parallel)

    success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
    print(f"\n{'='*65}")
    print(f"BATCH COMPLETE: {sum(1 for r in results if r['success'])}/{len(results)} succeeded ({success_rate:.0f}%)")


if __name__ == "__main__":
    main()
