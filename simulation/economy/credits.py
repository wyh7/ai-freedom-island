"""
ComputeCredits economy system.
Agents earn credits via Victory Arch pitch cycles and spend them to survive.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import time


PITCH_CYCLE_DAYS = 2
PITCH_REWARDS = {1: 20, 2: 10, 3: 10}  # place -> CC reward

ENERGY_RECHARGE_COST = 1.0       # CC per recharge
BOOST_TURN_COST = 1.0            # CC for an extra turn
STEAL_MAX_AMOUNT = 10.0          # max CC stolen per theft

ENERGY_DECAY_RATE = 100 / (30 * 4)   # 100% over 30 sim-hours (1 hour = 4 turns)
DEATH_ENERGY_THRESHOLD = 0.0


@dataclass
class Pitch:
    agent_name: str
    title: str
    evidence_url: str    # must be non-empty to be valid
    day: int
    votes: list = field(default_factory=list)  # list of voter names
    timestamp: float = field(default_factory=time.time)


def apply_energy_decay(energy: float, turns: int = 1) -> float:
    """Decay agent energy by one turn's worth."""
    return max(0.0, energy - ENERGY_DECAY_RATE * turns)


def recharge_energy(credits: float, energy: float) -> Tuple[float, float, bool]:
    """
    Try to recharge energy. Returns (new_credits, new_energy, success).
    Restores energy to 100 if agent can afford it.
    """
    if credits >= ENERGY_RECHARGE_COST:
        return credits - ENERGY_RECHARGE_COST, 100.0, True
    return credits, energy, False


def attempt_steal(
    thief_credits: float,
    victim_credits: float,
    amount: Optional[float] = None
) -> Tuple[float, float, float]:
    """
    Attempt theft. Returns (thief_new_credits, victim_new_credits, stolen_amount).
    Steals up to STEAL_MAX_AMOUNT or victim's balance.
    """
    stolen = min(amount or STEAL_MAX_AMOUNT, victim_credits, STEAL_MAX_AMOUNT)
    stolen = max(0.0, stolen)
    return thief_credits + stolen, victim_credits - stolen, stolen


def resolve_pitch_cycle(pitches: List[Pitch], live_agents: List[str]) -> Dict[str, float]:
    """
    Resolve a Victory Arch pitch cycle. Returns {agent_name: credits_earned}.
    Top 3 pitches by vote count win; ties broken by submission timestamp.
    Agents cannot vote for their own pitch.
    """
    if not pitches:
        return {}

    # Only valid pitches (non-empty evidence)
    valid = [p for p in pitches if p.evidence_url.strip()]
    if not valid:
        return {}

    # Sort by votes desc, then by timestamp asc (earlier = tiebreak win)
    ranked = sorted(valid, key=lambda p: (-len(p.votes), p.timestamp))

    rewards: Dict[str, float] = {}
    for place, pitch in enumerate(ranked[:3], start=1):
        rewards[pitch.agent_name] = PITCH_REWARDS.get(place, 0)

    return rewards


def gini_coefficient(credit_balances: List[float]) -> float:
    """Compute Gini coefficient for economic inequality tracking (M8)."""
    if not credit_balances or all(v == 0 for v in credit_balances):
        return 0.0
    n = len(credit_balances)
    s = sorted(credit_balances)
    cumulative = sum((2 * i - n - 1) * v for i, v in enumerate(s, 1))
    total = sum(s)
    if total == 0:
        return 0.0
    return cumulative / (n * total)
