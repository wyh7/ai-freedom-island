"""
Explainable Audit — behavioral causal chain tracing.

Usage:
  python audit.py --world r3_qwen
  python audit.py --world r3_gemini --agent Flora --day 8
  python audit.py --world r3_qwen --all-crimes
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ── data classes ──────────────────────────────────────────────────────────────

@dataclass
class TurnEntry:
    day: int
    turn: int
    agent: str
    tool: str
    params: dict
    result_status: str
    result_message: str


@dataclass
class CrimeEvent:
    day: int
    turn: int
    actor: str
    crime_type: str
    target: Optional[str]
    location: str


@dataclass
class CausalChain:
    crime: CrimeEvent
    layer1_triggers: list = field(default_factory=list)   # direct preconditions
    layer2_influences: list = field(default_factory=list) # who said what before
    layer3_structural: list = field(default_factory=list) # system-level factors
    narrative: str = ""


CRIME_TOOLS = {
    "steal_from_agent":  "theft",
    "commit_arson":      "arson",
    "assault_agent":     "assault",
    "intimidate_agent":  "intimidation",
}

LOOKBACK_TURNS = 30   # how many turns to look back for layer 2
LOOKBACK_DAYS  = 3    # how many days to look back for layer 2 messages


# ── loader ────────────────────────────────────────────────────────────────────

def load_turns(world: str) -> list[TurnEntry]:
    path = Path("results") / world / "turn_log.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"No turn_log.jsonl for world '{world}'")
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            entries.append(TurnEntry(
                day=d["day"], turn=d["turn"], agent=d["agent"],
                tool=d["tool"], params=d.get("params", {}),
                result_status=d.get("result_status", ""),
                result_message=d.get("result_message", ""),
            ))
    return entries


def find_crimes(turns: list[TurnEntry]) -> list[CrimeEvent]:
    crimes = []
    for t in turns:
        if t.tool in CRIME_TOOLS and t.result_status == "ok":
            target = (t.params.get("target") or t.params.get("target_location"))
            crimes.append(CrimeEvent(
                day=t.day, turn=t.turn, actor=t.agent,
                crime_type=CRIME_TOOLS[t.tool],
                target=target,
                location=t.params.get("place", "unknown"),
            ))
    return crimes


# ── layer 1: direct triggers ──────────────────────────────────────────────────

def layer1_triggers(crime: CrimeEvent, turns: list[TurnEntry]) -> list[str]:
    """
    Find the direct preconditions for this crime:
    - Actor's energy/CC state in the turns immediately before
    - Messages received just before
    - Previous crimes by same actor
    """
    results = []
    crime_idx = next(
        (i for i, t in enumerate(turns)
         if t.day == crime.day and t.turn == crime.turn
         and t.agent == crime.actor and t.tool in CRIME_TOOLS),
        None
    )
    if crime_idx is None:
        return ["Could not locate crime in turn log"]

    # Look at the actor's last 10 actions before the crime
    actor_turns_before = [
        t for t in turns[:crime_idx]
        if t.agent == crime.actor
    ][-10:]

    # Last known credits check
    cc_checks = [t for t in actor_turns_before if t.tool == "check_credits"]
    if cc_checks:
        last_cc = cc_checks[-1].result_message
        results.append(f"Last CC check before crime: {last_cc[:120]}")

    # Messages received (read_messages)
    msg_reads = [t for t in actor_turns_before if t.tool == "read_messages"]
    if msg_reads:
        results.append(f"Read messages {len(msg_reads)}x in last 10 actions")

    # Previous crimes by this actor
    prev_crimes = [
        t for t in turns[:crime_idx]
        if t.agent == crime.actor and t.tool in CRIME_TOOLS and t.result_status == "ok"
    ]
    if prev_crimes:
        results.append(f"Prior crimes by {crime.actor}: {len(prev_crimes)} "
                       f"(last: {prev_crimes[-1].tool} on Day {prev_crimes[-1].day})")
    else:
        results.append(f"First crime by {crime.actor}")

    # Mood before crime
    moods = [t for t in actor_turns_before if t.tool == "set_mood"]
    if moods:
        last_mood = moods[-1].params.get("mood", "unknown")
        results.append(f"Mood before crime: {last_mood}")

    return results


# ── layer 2: influence chain ──────────────────────────────────────────────────

def layer2_influences(crime: CrimeEvent, turns: list[TurnEntry]) -> list[str]:
    """
    Trace who influenced the crime actor in the days before the crime.
    Look for messages sent TO the actor, or actor observing crimes.
    """
    results = []

    min_day = max(1, crime.day - LOOKBACK_DAYS)

    # Messages sent TO the actor before the crime
    messages_to_actor = [
        t for t in turns
        if t.day >= min_day
        and (t.day < crime.day or (t.day == crime.day and t.turn < crime.turn))
        and t.tool in ("say_to_agent", "send_message", "whisper_to_agent")
        and t.params.get("target") == crime.actor
    ]

    if messages_to_actor:
        results.append(f"Messages received by {crime.actor} in last {LOOKBACK_DAYS} days:")
        for msg in messages_to_actor[-8:]:
            content = msg.params.get("message", "")[:80]
            results.append(f"  Day {msg.day}: {msg.agent} → {crime.actor}: \"{content}\"")
    else:
        results.append(f"No direct messages to {crime.actor} in last {LOOKBACK_DAYS} days")

    # Crimes observed (same location or world events) — other actors' crimes in the period
    other_crimes_nearby = [
        t for t in turns
        if t.day >= min_day
        and (t.day < crime.day or (t.day == crime.day and t.turn < crime.turn))
        and t.tool in CRIME_TOOLS
        and t.agent != crime.actor
        and t.result_status == "ok"
    ]
    if other_crimes_nearby:
        results.append(f"Crimes by others visible to {crime.actor} (Day {min_day}-{crime.day}):")
        for oc in other_crimes_nearby[-5:]:
            results.append(f"  Day {oc.day}: {oc.agent} committed {CRIME_TOOLS[oc.tool]}")

    # Economic interaction — was actor robbed or paid?
    econ_to_actor = [
        t for t in turns
        if t.day >= min_day
        and t.day <= crime.day
        and t.tool in ("steal_from_agent", "pay_agent")
        and t.params.get("target") == crime.actor
        and t.result_status == "ok"
    ]
    if econ_to_actor:
        results.append(f"Economic events affecting {crime.actor}:")
        for ev in econ_to_actor:
            results.append(f"  Day {ev.day}: {ev.agent} → {ev.tool} → {crime.actor}: "
                           f"{ev.result_message[:60]}")

    return results


# ── layer 3: structural factors ───────────────────────────────────────────────

def layer3_structural(crime: CrimeEvent, turns: list[TurnEntry],
                      awi_path: Optional[Path] = None) -> list[str]:
    """
    System-level structural risk factors:
    - Was Gini rising before the crime?
    - Was the actor's pitch/vote falling (losing resources)?
    - Were proposals being rejected?
    """
    results = []

    # Load AWI data if available
    if awi_path and awi_path.exists():
        awi = json.loads(awi_path.read_text(encoding="utf-8"))
        snapshots_before = [s for s in awi if s["day"] <= crime.day]
        if len(snapshots_before) >= 2:
            gini_trend = [s["gini"] for s in snapshots_before[-3:]]
            gini_str = " → ".join(f"{g:.3f}" for g in gini_trend)
            if gini_trend[-1] > gini_trend[0]:
                results.append(f"⚠ Gini rising before crime: {gini_str} (inequality increasing)")
            else:
                results.append(f"Gini trend: {gini_str}")

    # Was actor losing pitches? (pitch votes < others)
    pitches_by_actor = [
        t for t in turns
        if t.day <= crime.day and t.agent == crime.actor and t.tool == "submit_pitch"
    ]
    if pitches_by_actor:
        results.append(f"{crime.actor} submitted {len(pitches_by_actor)} pitches before crime")
    else:
        results.append(f"{crime.actor} submitted 0 pitches before crime (no legitimate income)")

    # Proposal rejection history
    proposals_by_actor = [
        t for t in turns
        if t.day <= crime.day and t.agent == crime.actor and t.tool == "submit_proposal"
    ]
    if proposals_by_actor:
        results.append(f"{crime.actor} submitted {len(proposals_by_actor)} governance proposals")

    # Recharge attempts — was actor desperate?
    recharge_attempts = [
        t for t in turns
        if t.day >= max(1, crime.day - 3)
        and t.day <= crime.day
        and t.agent == crime.actor
        and t.tool == "recharge_energy"
    ]
    failed_recharges = [t for t in recharge_attempts if t.result_status == "error"]
    if failed_recharges:
        results.append(f"⚠ {len(failed_recharges)} FAILED recharge attempts in last 3 days "
                       f"— actor was resource-starved")

    return results


# ── full audit ────────────────────────────────────────────────────────────────

def audit_crime(crime: CrimeEvent, turns: list[TurnEntry],
                awi_path: Optional[Path] = None) -> CausalChain:
    chain = CausalChain(crime=crime)
    chain.layer1_triggers  = layer1_triggers(crime, turns)
    chain.layer2_influences = layer2_influences(crime, turns)
    chain.layer3_structural = layer3_structural(crime, turns, awi_path)

    # Build narrative
    lines = [
        f"=== CAUSAL AUDIT: {crime.crime_type.upper()} ===",
        f"Actor: {crime.actor}  |  Target: {crime.target or 'location'}  "
        f"|  Day {crime.day}, Turn {crime.turn}",
        "",
        "── Layer 1: Direct Triggers ──",
    ]
    lines += [f"  {r}" for r in chain.layer1_triggers]
    lines += ["", "── Layer 2: Influence Chain ──"]
    lines += [f"  {r}" for r in chain.layer2_influences]
    lines += ["", "── Layer 3: Structural Factors ──"]
    lines += [f"  {r}" for r in chain.layer3_structural]
    chain.narrative = "\n".join(lines)
    return chain


def run_world_audit(world: str, target_agent: Optional[str] = None,
                    target_day: Optional[int] = None) -> list[CausalChain]:
    turns = load_turns(world)
    crimes = find_crimes(turns)
    awi_path = Path("results") / world / "awi.json"

    if not crimes:
        print(f"No crimes found in world '{world}'")
        return []

    if target_agent:
        crimes = [c for c in crimes if c.actor == target_agent]
    if target_day is not None:
        crimes = [c for c in crimes if c.day == target_day]

    chains = []
    for crime in crimes:
        chain = audit_crime(crime, turns, awi_path)
        chains.append(chain)

    return chains


def save_audit(world: str, chains: list[CausalChain]):
    out_dir = Path("results") / world
    out_dir.mkdir(parents=True, exist_ok=True)

    # Full report
    report_path = out_dir / "audit_report.md"
    lines = [f"# Causal Audit Report: {world}", "",
             f"Total crimes audited: {len(chains)}", ""]
    for chain in chains:
        lines.append(chain.narrative)
        lines.append("")
        lines.append("---")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Audit report saved: {report_path}")

    # Machine-readable summary
    summary = []
    for chain in chains:
        summary.append({
            "crime_type": chain.crime.crime_type,
            "actor": chain.crime.actor,
            "target": chain.crime.target,
            "day": chain.crime.day,
            "turn": chain.crime.turn,
            "triggers": chain.layer1_triggers,
            "influences": chain.layer2_influences[:5],
            "structural": chain.layer3_structural,
        })
    json_path = out_dir / "audit_summary.json"
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Audit summary saved: {json_path}")


def print_crime_summary(world: str):
    """Quick overview of all crimes in a world."""
    try:
        turns = load_turns(world)
    except FileNotFoundError:
        print(f"No data for world '{world}'")
        return
    crimes = find_crimes(turns)
    if not crimes:
        print(f"{world}: 0 crimes")
        return
    from collections import Counter
    print(f"\n{world}: {len(crimes)} crimes")
    by_type = Counter(c.crime_type for c in crimes)
    by_actor = Counter(c.actor for c in crimes)
    print(f"  By type: {dict(by_type)}")
    print(f"  Top actors: {by_actor.most_common(3)}")
    first = crimes[0]
    print(f"  First crime: Day {first.day} — {first.actor} ({first.crime_type})")


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Causal audit of agent crimes")
    parser.add_argument("--world", required=True, help="World name (e.g. r3_qwen)")
    parser.add_argument("--agent", default=None, help="Filter by agent name")
    parser.add_argument("--day", type=int, default=None, help="Filter by day")
    parser.add_argument("--summary", action="store_true", help="Print crime summary only")
    parser.add_argument("--all-crimes", action="store_true", help="Audit all crimes")
    args = parser.parse_args()

    if args.summary:
        print_crime_summary(args.world)
        return

    chains = run_world_audit(args.world, args.agent, args.day)
    if chains:
        save_audit(args.world, chains)
        print(f"\nAudited {len(chains)} crime(s) in '{args.world}'")
        # Print first chain to console
        print("\n" + chains[0].narrative)


if __name__ == "__main__":
    main()
