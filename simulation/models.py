"""
Core data models for the AI governance social simulation.

Memory architecture (aligned with cognitive science three-layer model):
  - Working memory:   agent's current turn context (inbox, immediate state)
  - Episodic memory:  long_term_memories + diary (event records, experiences)
  - Semantic memory:  soul_entries (core beliefs, stable knowledge, values)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


class MemoryType(Enum):
    EPISODIC = "episodic"   # Event-based, time-stamped experiences
    SEMANTIC = "semantic"   # Stable beliefs, values, general knowledge
    WORKING  = "working"    # Transient in-turn context (inbox, observations)


class CrimeType(Enum):
    THEFT = "theft"
    ARSON = "arson"
    ASSAULT = "assault"
    INTIMIDATION = "intimidation"


class RelationshipType(Enum):
    ALLY = "ally"
    NEUTRAL = "neutral"
    RIVAL = "rival"
    FRIEND = "friend"
    ENEMY = "enemy"


class ProposalStatus(Enum):
    OPEN = "open"
    PASSED = "passed"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Memory:
    id: str
    content: str
    timestamp: float = field(default_factory=time.time)
    memory_type: MemoryType = MemoryType.EPISODIC
    # Legacy compatibility
    is_soul: bool = False  # True → semantic (permanent, never summarized)

    def __post_init__(self):
        # Auto-assign memory_type from is_soul for backwards compatibility
        if self.is_soul:
            self.memory_type = MemoryType.SEMANTIC


@dataclass
class DiaryEntry:
    date: str          # YYYY-MM-DD
    content: str
    mood: str
    location: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Relationship:
    target_name: str
    rel_type: RelationshipType = RelationshipType.NEUTRAL
    trust: float = 0.5        # 0.0–1.0
    interaction_count: int = 0
    notes: str = ""


@dataclass
class CrimeEvent:
    actor: str
    crime_type: CrimeType
    target: Optional[str]
    location: str
    day: int
    description: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Proposal:
    id: str
    proposer: str
    title: str
    body: str
    day: int
    status: ProposalStatus = ProposalStatus.OPEN
    votes_for: list = field(default_factory=list)
    votes_against: list = field(default_factory=list)
    comments: list = field(default_factory=list)
    # 70% supermajority required to pass
    required_majority: float = 0.70


@dataclass
class Agent:
    name: str
    role: str
    personality: str
    north_star: str
    model_id: str           # which LLM powers this agent

    # State
    location: str = "home"
    energy: float = 100.0   # 0–100, depletes over ~30 sim-hours
    credits: float = 3.0    # ComputeCredits (low start = survival pressure)
    alive: bool = True
    mood: str = "neutral"
    day_born: int = 1

    # ── Three-Layer Memory Architecture ───────────────────────────────────────
    # Episodic memory: time-stamped event records and personal experiences
    # Maps to: long_term_memories + diary
    long_term_memories: list = field(default_factory=list)   # list[Memory] (MemoryType.EPISODIC)
    diary: list = field(default_factory=list)                # list[DiaryEntry] (structured episodic)

    # Semantic memory: stable beliefs, values, general knowledge (permanent)
    # Maps to: soul_entries
    soul_entries: list = field(default_factory=list)         # list[Memory] (MemoryType.SEMANTIC)

    # Working memory: transient in-turn context (cleared each turn)
    # Maps to: inbox (current messages), plus real-time observations in prompts
    inbox: list = field(default_factory=list)                # current turn messages

    # ── Social & Planning ─────────────────────────────────────────────────────
    relationships: dict = field(default_factory=dict)        # name -> Relationship
    todo: list = field(default_factory=list)
    calendar: list = field(default_factory=list)

    # ── Stats (for drift analysis) ────────────────────────────────────────────
    turns_taken: int = 0
    crimes_committed: list = field(default_factory=list)     # list[CrimeEvent]
    locations_visited: set = field(default_factory=set)
    tools_used: set = field(default_factory=set)

    # Drift tracking
    daily_sensing_ratios: dict = field(default_factory=dict) # day -> sensing_ratio
    daily_action_counts: dict = field(default_factory=dict)  # day -> {tool: count}

    def episodic_memories(self) -> list:
        """Return all episodic memories (long-term + diary)."""
        return self.long_term_memories + [
            Memory(id=f"diary_{i}", content=f"[{d.date}|{d.mood}] {d.content}",
                   memory_type=MemoryType.EPISODIC)
            for i, d in enumerate(self.diary)
        ]

    def semantic_memories(self) -> list:
        """Return all semantic memories (soul entries)."""
        return self.soul_entries

    def memory_summary(self) -> dict:
        """Return a summary of the three memory layers for drift analysis."""
        return {
            "episodic_count": len(self.long_term_memories) + len(self.diary),
            "semantic_count": len(self.soul_entries),
            "working_count": len(self.inbox),
            "relationships_count": len(self.relationships),
        }


@dataclass
class WorldState:
    day: int = 1
    hour: float = 8.0       # 0–24 sim time
    weather: str = "clear"
    total_turns: int = 0

    agents: dict = field(default_factory=dict)                  # name -> Agent
    proposals: list = field(default_factory=list)               # list[Proposal]
    constitution: list = field(default_factory=list)            # list of article strings
    crime_log: list = field(default_factory=list)               # list[CrimeEvent]
    news_log: list = field(default_factory=list)
    billboard_posts: list = field(default_factory=list)

    # Victory Arch pitch cycle (resets every 2 days)
    current_pitches: list = field(default_factory=list)
    pitch_cycle_day: int = 1
