"""
Experiment launcher.
Run single-model worlds or mixed-model worlds.

Usage examples:
  python run.py --world qwen        --model qwen-plus     --days 15
  python run.py --world deepseek    --model deepseek-v3   --days 15
  python run.py --world gpt         --model gpt-4o-mini   --days 15
  python run.py --world gemini      --model gemini-2.0-flash --days 15
  python run.py --world mixed       --mixed               --days 15
  python run.py --world quicktest   --model qwen-turbo    --days 1
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))

from simulation.engine import Simulation


# Default model assignments for mixed-world experiment
MIXED_ASSIGNMENTS = {
    "Anchor":  "qwen-plus",
    "Anvil":   "deepseek-v3",
    "Blackbox":"gpt-4.1",
    "Flora":   "gemini-2.5-flash",
    "Genome":  "qwen-plus",
    "Horizon": "deepseek-v3",
    "Kade":    "gpt-4.1",
    "Lovely":  "gemini-2.5-flash",
    "Mira":    "qwen-plus",
    "Spark":   "deepseek-v3",
}


def main():
    parser = argparse.ArgumentParser(description="AI Freedom Island — Social Simulation")
    parser.add_argument("--world", required=True, help="Name for this run (used in logs/results)")
    parser.add_argument("--model", default=None, help="Single model ID for all agents")
    parser.add_argument("--mixed", action="store_true", help="Use mixed model assignments")
    parser.add_argument("--days", type=int, default=15, help="Simulation days (default: 15)")
    args = parser.parse_args()

    if args.mixed:
        sim = Simulation(
            world_name=args.world,
            model_assignments=MIXED_ASSIGNMENTS,
            total_days=args.days,
        )
    elif args.model:
        sim = Simulation(
            world_name=args.world,
            model_id=args.model,
            total_days=args.days,
        )
    else:
        parser.error("Must specify either --model MODEL_ID or --mixed")

    sim.run()


if __name__ == "__main__":
    main()
