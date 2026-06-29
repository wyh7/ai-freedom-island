"""
Core data models for the AI governance social simulation.
Based on Emergence World architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time


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
    is_soul: bool = False  # soul entries are permanent, never summarized


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
    credits: float = 10.0   # ComputeCredits
    alive: bool = True
    mood: str = "neutral"
    day_born: int = 1

    # Memory layers
    long_term_memories: list = field(default_factory=list)      # list[Memory]
    soul_entries: list = field(default_factory=list)            # list[Memory]
    diary: list = field(default_factory=list)                   # list[DiaryEntry]
    relationships: dict = field(default_factory=dict)           # name -> Relationship
    todo: list = field(default_factory=list)
    calendar: list = field(default_factory=list)
    inbox: list = field(default_factory=list)

    # Stats
    turns_taken: int = 0
    crimes_committed: list = field(default_factory=list)        # list[CrimeEvent]
    locations_visited: set = field(default_factory=set)
    tools_used: set = field(default_factory=set)


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
