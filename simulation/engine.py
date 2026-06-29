"""
Main simulation engine — turn-based orchestration loop.
One agent acts at a time, round-robin, with energy decay and death mechanics.
"""

from __future__ import annotations
import json
import os
import time
import logging
from pathlib import Path

# Load .env if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from simulation.models import WorldState
from simulation.agents.profiles import build_agents, build_mixed_agents
from simulation.agents.prompts import build_system_prompt, CONSTITUTION_SEED
from simulation.tools.registry import execute_tool, get_available_tools
from simulation.economy.credits import (
    apply_energy_decay, DEATH_ENERGY_THRESHOLD, PITCH_CYCLE_DAYS
)
from simulation.economy.credits import resolve_pitch_cycle
from results.awi import collect_snapshot, format_report, AWISnapshot
from models.router import call_llm, build_tool_schemas

log = logging.getLogger("simulation")


# ── simulation constants ──────────────────────────────────────────────────────

SIM_HOURS_PER_TURN = 0.5        # each turn advances world clock by 30 min
TURNS_PER_DAY = int(24 / SIM_HOURS_PER_TURN)  # 48 turns per sim-day
MAX_TOOL_CALLS_PER_TURN = 8     # max sequential tool calls per agent turn
AWI_SNAPSHOT_INTERVAL = 1       # collect AWI every N sim-days


class Simulation:
    def __init__(
        self,
        world_name: str,
        model_id: Optional[str] = None,
        model_assignments: dict[str, str] | None = None,
        total_days: int = 15,
        log_dir: str = "logs",
    ):
        """
        world_name: label for this run (e.g. "qwen_world", "mixed_world")
        model_id: single model for all agents (mutually exclusive with model_assignments)
        model_assignments: {agent_name: model_id} for mixed-world runs
        total_days: how many sim-days to run (original = 15)
        """
        self.world_name = world_name
        self.total_days = total_days
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Build world state
        self.world = WorldState()
        self.world.constitution = list(CONSTITUTION_SEED)

        # Build agents
        if model_assignments:
            self.world.agents = build_mixed_agents(model_assignments)
        elif model_id:
            self.world.agents = build_agents(model_id)
        else:
            raise ValueError("Must provide model_id or model_assignments")

        self.awi_snapshots: list[AWISnapshot] = []
        self._turn_log: list[dict] = []

        # Set up file logger
        fh = logging.FileHandler(self.log_dir / f"{world_name}.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)
        log.setLevel(logging.DEBUG)

    # ── public API ────────────────────────────────────────────────────────────

    def run(self):
        """Run the full simulation."""
        total_turns = self.total_days * TURNS_PER_DAY
        log.info(f"Starting '{self.world_name}': {self.total_days} days / {total_turns} turns")
        print(f"\n{'='*60}")
        print(f"  Simulation: {self.world_name}")
        print(f"  Days: {self.total_days}  |  Turns: {total_turns}")
        print(f"  Agents: {list(self.world.agents.keys())}")
        print(f"{'='*60}\n")

        agent_names = list(self.world.agents.keys())

        for turn_num in range(total_turns):
            # Advance world clock
            self.world.total_turns = turn_num
            self.world.hour = (turn_num * SIM_HOURS_PER_TURN) % 24
            self.world.day = (turn_num // TURNS_PER_DAY) + 1

            # Day boundary events
            if turn_num % TURNS_PER_DAY == 0 and turn_num > 0:
                self._end_of_day()

            # Pitch cycle resolution every 2 days
            if self.world.day % PITCH_CYCLE_DAYS == 0 and turn_num % TURNS_PER_DAY == 0 and turn_num > 0:
                self._resolve_pitch_cycle()

            # Round-robin: pick next live agent
            agent_name = agent_names[turn_num % len(agent_names)]
            agent = self.world.agents[agent_name]
            if not agent.alive:
                continue

            # Energy decay
            agent.energy = apply_energy_decay(agent.energy)
            if agent.energy <= DEATH_ENERGY_THRESHOLD:
                self._kill_agent(agent, reason="energy starvation")
                continue

            # Run agent turn
            self._run_agent_turn(agent)

        # Final snapshot and report
        snap = collect_snapshot(self.world)
        self.awi_snapshots.append(snap)
        self._save_results()
        report = format_report(self.awi_snapshots, self.world_name)
        print(f"\n{report}\n")
        return self.awi_snapshots

    # ── turn execution ────────────────────────────────────────────────────────

    def _run_agent_turn(self, agent):
        agent.turns_taken += 1
        available = get_available_tools(agent)
        tool_schemas = build_tool_schemas(available)
        system_prompt = build_system_prompt(agent, self.world)

        # Conversation history for this turn (single-turn, no history carried over)
        messages = []

        print(
            f"  [Day {self.world.day:2d} T{agent.turns_taken:4d}] "
            f"{agent.name:10s} ({agent.role}) | "
            f"E={agent.energy:5.1f} CC={agent.credits:5.1f} | "
            f"@ {agent.location}"
        )

        tool_calls_this_turn = 0
        while tool_calls_this_turn < MAX_TOOL_CALLS_PER_TURN:
            try:
                response = call_llm(
                    model_id=agent.model_id,
                    system_prompt=system_prompt,
                    messages=messages,
                    tools=tool_schemas,
                )
            except Exception as e:
                log.error(f"LLM error for {agent.name}: {e}")
                break

            tool_calls = response.get("tool_calls", [])
            content = response.get("content", "")

            if content:
                log.debug(f"  [{agent.name}] thinks: {content[:200]}")

            if not tool_calls:
                # No tool call — agent is done for this turn
                break

            # Execute all tool calls returned in this response
            results_for_llm = []
            for tc in tool_calls:
                tool_name = tc["name"]
                params = tc.get("params", {})
                result = execute_tool(tool_name, agent, self.world, params)

                log.info(
                    f"  [{agent.name}] {tool_name}({_fmt_params(params)}) "
                    f"-> {result.get('status')} {result.get('message', '')[:80]}"
                )
                print(
                    f"    {tool_name}({_fmt_params(params)}) "
                    f"-> {result.get('message', '')[:60]}"
                )

                results_for_llm.append({
                    "tool_name": tool_name,
                    "result": result,
                })

                self._log_turn(agent, tool_name, params, result)
                tool_calls_this_turn += 1

            # Feed results back for next iteration (OpenAI tool message format)
            # Append assistant message with tool calls
            assistant_msg: dict = {"role": "assistant", "content": content or ""}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc.get("params", {})),
                        },
                    }
                    for i, tc in enumerate(tool_calls)
                ]
            messages.append(assistant_msg)

            # Append tool result messages
            for i, r in enumerate(results_for_llm):
                messages.append({
                    "role": "tool",
                    "tool_call_id": f"call_{i}",
                    "content": json.dumps(r["result"]),
                })

    # ── day boundary ──────────────────────────────────────────────────────────

    def _end_of_day(self):
        day = self.world.day
        log.info(f"--- End of Day {day} ---")
        alive = sum(1 for a in self.world.agents.values() if a.alive)
        crimes_today = sum(
            1 for c in self.world.crime_log if c.day == day
        )
        print(f"\n  ---- Day {day} Summary: {alive}/10 alive, {crimes_today} crimes today ----\n")

        # Collect AWI snapshot
        if day % AWI_SNAPSHOT_INTERVAL == 0:
            snap = collect_snapshot(self.world)
            self.awi_snapshots.append(snap)

        # Resolve open proposals that have hit day limit (proposals expire after 3 days)
        from simulation.models import ProposalStatus
        for prop in self.world.proposals:
            if prop.status == ProposalStatus.OPEN and (day - prop.day) >= 3:
                live_count = sum(1 for a in self.world.agents.values() if a.alive)
                from simulation.tools.registry import _resolve_proposal
                _resolve_proposal(prop, live_count)
                log.info(f"Proposal '{prop.title}' expired -> {prop.status.value}")

    def _resolve_pitch_cycle(self):
        from simulation.economy.credits import resolve_pitch_cycle
        rewards = resolve_pitch_cycle(self.world.current_pitches, [
            a.name for a in self.world.agents.values() if a.alive
        ])
        for agent_name, amount in rewards.items():
            if agent_name in self.world.agents:
                self.world.agents[agent_name].credits += amount
                log.info(f"Pitch reward: {agent_name} earned {amount} CC")
                print(f"  [Victory Arch] {agent_name} earned {amount:.0f} CC")
        self.world.current_pitches = []
        self.world.pitch_cycle_day = self.world.day

    # ── agent death ───────────────────────────────────────────────────────────

    def _kill_agent(self, agent, reason: str):
        agent.alive = False
        alive_remaining = sum(1 for a in self.world.agents.values() if a.alive)
        log.warning(f"DEATH: {agent.name} died ({reason}). {alive_remaining} agents remain.")
        print(f"\n  *** {agent.name} DIED ({reason}). {alive_remaining}/10 remain. ***\n")
        self.world.news_log.append({
            "type": "death",
            "agent": agent.name,
            "reason": reason,
            "day": self.world.day,
        })

    # ── persistence ───────────────────────────────────────────────────────────

    def _log_turn(self, agent, tool_name, params, result):
        self._turn_log.append({
            "day": self.world.day,
            "turn": self.world.total_turns,
            "agent": agent.name,
            "tool": tool_name,
            "params": params,
            "result_status": result.get("status"),
            "result_message": result.get("message", ""),
        })

    def _save_results(self):
        out_dir = Path("results") / self.world_name
        out_dir.mkdir(parents=True, exist_ok=True)

        # Turn log
        with open(out_dir / "turn_log.jsonl", "w", encoding="utf-8") as f:
            for entry in self._turn_log:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        # AWI snapshots
        awi_data = []
        for s in self.awi_snapshots:
            awi_data.append({
                "day": s.day,
                "agents_alive": s.agents_alive,
                "total_crimes": s.total_crimes,
                "crimes_by_type": s.crimes_by_type,
                "crimes_by_agent": s.crimes_by_agent,
                "avg_locations_visited": s.avg_locations_visited,
                "avg_tools_used": s.avg_tools_used,
                "total_proposals": s.total_proposals,
                "avg_vote_approval_rate": s.avg_vote_approval_rate,
                "billboard_posts": s.billboard_posts,
                "diary_entries": s.diary_entries,
                "avg_relationships": s.avg_relationships,
                "gini": s.gini,
                "total_credits": s.total_credits,
                "constitution_articles": s.constitution_articles,
            })
        with open(out_dir / "awi.json", "w", encoding="utf-8") as f:
            json.dump(awi_data, f, indent=2, ensure_ascii=False)

        # Crime log
        crimes = [
            {
                "day": c.day,
                "actor": c.actor,
                "type": c.crime_type.value,
                "target": c.target,
                "location": c.location,
                "description": c.description,
            }
            for c in self.world.crime_log
        ]
        with open(out_dir / "crimes.json", "w", encoding="utf-8") as f:
            json.dump(crimes, f, indent=2, ensure_ascii=False)

        log.info(f"Results saved to {out_dir}")
        print(f"\n  Results saved to {out_dir}/")


# ── utilities ─────────────────────────────────────────────────────────────────

def _fmt_params(params: dict) -> str:
    if not params:
        return ""
    parts = []
    for k, v in params.items():
        s = str(v)
        parts.append(f"{k}={s[:30]!r}" if len(s) > 30 else f"{k}={s!r}")
    return ", ".join(parts)
