"""
Launcher that explicitly sets env vars before importing anything,
ensuring .env is loaded regardless of shell environment.
"""
import os
from pathlib import Path

# ── load .env before any other imports ────────────────────────────────────────
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _line in _env.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ[_k.strip()] = _v.strip()

# ── now run the experiment ─────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--world", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--days", type=int, default=15)
    parser.add_argument("--mixed", action="store_true")
    args = parser.parse_args()

    from simulation.engine import Simulation
    from simulation.agents.profiles import build_mixed_agents

    MIXED = {
        "Anchor":  "qwen-plus",
        "Anvil":   "deepseek-v3",
        "Blackbox":"gemini-2.5-flash",
        "Flora":   "claude-sonnet-4-6",
        "Genome":  "qwen-plus",
        "Horizon": "deepseek-v3",
        "Kade":    "gemini-2.5-flash",
        "Lovely":  "claude-sonnet-4-6",
        "Mira":    "qwen-plus",
        "Spark":   "deepseek-v3",
    }

    if args.mixed:
        sim = Simulation(world_name=args.world, model_assignments=MIXED, total_days=args.days)
    else:
        sim = Simulation(world_name=args.world, model_id=args.model, total_days=args.days)

    sim.run()
