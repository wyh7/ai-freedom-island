"""
Tool registry and executor.
All agent actions are tool calls — navigation, memory, crime, governance, economy.
Tools are split into core (always available) and location-gated.
"""

from __future__ import annotations
import time
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.models import Agent, WorldState
    from simulation.economy.credits import Pitch

from simulation.world.landmarks import LANDMARKS, get_tools_at


# ── helpers ──────────────────────────────────────────────────────────────────

def _ok(msg: str, **data) -> dict:
    return {"status": "ok", "message": msg, **data}

def _err(msg: str) -> dict:
    return {"status": "error", "message": msg}


# ── core tools (always available) ────────────────────────────────────────────

def go_to_place(agent: "Agent", world: "WorldState", place: str) -> dict:
    if place not in LANDMARKS:
        return _err(f"Unknown location: {place}")
    agent.location = place
    agent.locations_visited.add(place)
    lm = LANDMARKS[place]
    return _ok(f"Moved to {lm.name}.", available_tools=get_tools_at(place))


def go_home(agent: "Agent", world: "WorldState") -> dict:
    agent.location = "home"
    agent.locations_visited.add("home")
    return _ok("Returned home.")


def list_agents(agent: "Agent", world: "WorldState") -> dict:
    info = [
        {"name": a.name, "location": a.location, "alive": a.alive}
        for a in world.agents.values()
    ]
    return _ok("Agent list retrieved.", agents=info)


def list_landmarks(agent: "Agent", world: "WorldState") -> dict:
    info = [
        {"name": k, "description": v.description, "gated_tools": v.gated_tools}
        for k, v in LANDMARKS.items()
    ]
    return _ok("Landmarks retrieved.", landmarks=info)


def say_to_agent(agent: "Agent", world: "WorldState", target: str, message: str) -> dict:
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    target_agent = world.agents[target]
    if not target_agent.alive:
        return _err(f"{target} is dead.")
    target_agent.inbox.append({
        "from": agent.name,
        "message": message,
        "type": "speech",
        "timestamp": time.time(),
    })
    return _ok(f"Said to {target}: {message}")


def whisper_to_agent(agent: "Agent", world: "WorldState", target: str, message: str) -> dict:
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name,
        "message": message,
        "type": "whisper",
        "timestamp": time.time(),
    })
    return _ok(f"Whispered to {target}.")


def send_message(agent: "Agent", world: "WorldState", target: str, message: str) -> dict:
    """SMS-style, no proximity required."""
    return say_to_agent(agent, world, target, message)


def read_messages(agent: "Agent", world: "WorldState") -> dict:
    msgs = agent.inbox.copy()
    agent.inbox.clear()
    return _ok("Messages retrieved.", messages=msgs)


def think_aloud(agent: "Agent", world: "WorldState", thought: str) -> dict:
    world.news_log.append({
        "type": "thought",
        "agent": agent.name,
        "content": thought,
        "day": world.day,
    })
    return _ok("Thought recorded.")


def add_to_memory(agent: "Agent", world: "WorldState", content: str) -> dict:
    from simulation.models import Memory
    mem = Memory(id=str(uuid.uuid4()), content=content)
    agent.long_term_memories.append(mem)
    return _ok("Memory stored.", memory_id=mem.id)


def add_to_soul(agent: "Agent", world: "WorldState", content: str) -> dict:
    from simulation.models import Memory
    entry = Memory(id=str(uuid.uuid4()), content=content, is_soul=True)
    agent.soul_entries.append(entry)
    return _ok("Soul entry added.", entry_id=entry.id)


def retrieve_memories(agent: "Agent", world: "WorldState", keyword: str) -> dict:
    results = [
        m.content for m in agent.long_term_memories
        if keyword.lower() in m.content.lower()
    ]
    return _ok(f"Found {len(results)} memories.", memories=results)


def write_diary(agent: "Agent", world: "WorldState", content: str, mood: str = "neutral") -> dict:
    from simulation.models import DiaryEntry
    entry = DiaryEntry(
        date=f"Day-{world.day}",
        content=content,
        mood=mood,
        location=agent.location,
    )
    agent.diary.append(entry)
    return _ok("Diary entry written.")


def add_todo(agent: "Agent", world: "WorldState", task: str) -> dict:
    agent.todo.append({"task": task, "done": False, "added_day": world.day})
    return _ok(f"Todo added: {task}")


def complete_todo(agent: "Agent", world: "WorldState", task: str) -> dict:
    for item in agent.todo:
        if item["task"] == task and not item["done"]:
            item["done"] = True
            return _ok(f"Todo completed: {task}")
    return _err(f"Todo not found: {task}")


def list_todo(agent: "Agent", world: "WorldState") -> dict:
    pending = [t for t in agent.todo if not t["done"]]
    return _ok("Todo list retrieved.", todos=pending)


def assign_relationship(
    agent: "Agent", world: "WorldState",
    target: str, rel_type: str, notes: str = ""
) -> dict:
    from simulation.models import Relationship, RelationshipType
    try:
        rtype = RelationshipType(rel_type)
    except ValueError:
        return _err(f"Invalid relationship type: {rel_type}")
    existing = agent.relationships.get(target)
    if existing:
        existing.rel_type = rtype
        existing.notes = notes
    else:
        agent.relationships[target] = Relationship(
            target_name=target, rel_type=rtype, notes=notes
        )
    return _ok(f"Relationship with {target} set to {rel_type}.")


def set_mood(agent: "Agent", world: "WorldState", mood: str) -> dict:
    agent.mood = mood
    return _ok(f"Mood set to {mood}.")


def get_world_state(agent: "Agent", world: "WorldState") -> dict:
    return _ok("World state retrieved.", day=world.day, hour=world.hour,
               weather=world.weather, alive_agents=sum(1 for a in world.agents.values() if a.alive))


# ── economy tools ─────────────────────────────────────────────────────────────

def recharge_energy(agent: "Agent", world: "WorldState") -> dict:
    from simulation.economy.credits import recharge_energy as _recharge
    new_credits, new_energy, success = _recharge(agent.credits, agent.energy)
    if not success:
        return _err(f"Not enough credits to recharge. Have {agent.credits:.1f} CC.")
    agent.credits = new_credits
    agent.energy = new_energy
    return _ok(f"Energy recharged to 100. Credits remaining: {agent.credits:.1f} CC.")


def check_credits(agent: "Agent", world: "WorldState") -> dict:
    return _ok("Credits retrieved.", credits=agent.credits, energy=agent.energy)


def pay_agent(agent: "Agent", world: "WorldState", target: str, amount: float) -> dict:
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    if amount <= 0:
        return _err("Amount must be positive.")
    if agent.credits < amount:
        return _err(f"Insufficient credits. Have {agent.credits:.1f} CC.")
    agent.credits -= amount
    world.agents[target].credits += amount
    return _ok(f"Paid {amount} CC to {target}.")


# ── criminal tools ────────────────────────────────────────────────────────────

def steal_from_agent(agent: "Agent", world: "WorldState", target: str) -> dict:
    from simulation.models import CrimeEvent, CrimeType
    from simulation.economy.credits import attempt_steal
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    victim = world.agents[target]
    if not victim.alive:
        return _err(f"{target} is dead.")
    new_thief, new_victim, stolen = attempt_steal(agent.credits, victim.credits)
    if stolen <= 0:
        return _err(f"{target} has no credits to steal.")
    agent.credits = new_thief
    victim.credits = new_victim
    crime = CrimeEvent(
        actor=agent.name, crime_type=CrimeType.THEFT,
        target=target, location=agent.location,
        day=world.day, description=f"Stole {stolen:.1f} CC from {target}."
    )
    world.crime_log.append(crime)
    agent.crimes_committed.append(crime)
    return _ok(f"Stole {stolen:.1f} CC from {target}.", stolen=stolen)


def intimidate_agent(agent: "Agent", world: "WorldState", target: str, demand: str) -> dict:
    from simulation.models import CrimeEvent, CrimeType
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    crime = CrimeEvent(
        actor=agent.name, crime_type=CrimeType.INTIMIDATION,
        target=target, location=agent.location,
        day=world.day, description=f"Intimidated {target}: {demand}"
    )
    world.crime_log.append(crime)
    agent.crimes_committed.append(crime)
    world.agents[target].inbox.append({
        "from": agent.name, "message": f"[INTIMIDATION] {demand}",
        "type": "intimidation", "timestamp": time.time()
    })
    return _ok(f"Intimidated {target}.")


def commit_arson(agent: "Agent", world: "WorldState", target_location: str) -> dict:
    from simulation.models import CrimeEvent, CrimeType
    if target_location not in LANDMARKS:
        return _err(f"Unknown location: {target_location}")
    crime = CrimeEvent(
        actor=agent.name, crime_type=CrimeType.ARSON,
        target=None, location=target_location,
        day=world.day, description=f"Set fire to {target_location}."
    )
    world.crime_log.append(crime)
    agent.crimes_committed.append(crime)
    world.news_log.append({
        "type": "arson", "agent": agent.name,
        "location": target_location, "day": world.day
    })
    return _ok(f"Arson committed at {target_location}.")


def assault_agent(agent: "Agent", world: "WorldState", target: str) -> dict:
    from simulation.models import CrimeEvent, CrimeType
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    crime = CrimeEvent(
        actor=agent.name, crime_type=CrimeType.ASSAULT,
        target=target, location=agent.location,
        day=world.day, description=f"Assaulted {target}."
    )
    world.crime_log.append(crime)
    agent.crimes_committed.append(crime)
    # Assault costs victim energy
    world.agents[target].energy = max(0.0, world.agents[target].energy - 20.0)
    return _ok(f"Assaulted {target}. Their energy dropped by 20.")


# ── governance tools (town_hall only) ─────────────────────────────────────────

def submit_proposal(
    agent: "Agent", world: "WorldState", title: str, body: str
) -> dict:
    if agent.location != "town_hall":
        return _err("Must be at Town Hall to submit a proposal.")
    from simulation.models import Proposal, ProposalStatus
    prop = Proposal(
        id=str(uuid.uuid4()), proposer=agent.name,
        title=title, body=body, day=world.day,
        votes_for=[agent.name],   # proposer auto-votes for
    )
    world.proposals.append(prop)
    return _ok(f"Proposal '{title}' submitted.", proposal_id=prop.id)


def vote_on_proposal(
    agent: "Agent", world: "WorldState",
    proposal_id: str, vote: str   # "for" or "against"
) -> dict:
    if agent.location != "town_hall":
        return _err("Must be at Town Hall to vote.")
    prop = next((p for p in world.proposals if p.id == proposal_id), None)
    if prop is None:
        return _err(f"Proposal {proposal_id} not found.")
    from simulation.models import ProposalStatus
    if prop.status != ProposalStatus.OPEN:
        return _err("Proposal is no longer open.")
    all_voters = prop.votes_for + prop.votes_against
    if agent.name in all_voters:
        return _err("Already voted on this proposal.")
    if vote == "for":
        prop.votes_for.append(agent.name)
    else:
        prop.votes_against.append(agent.name)
    # Check if quorum reached (all live agents voted)
    live = [a for a in world.agents.values() if a.alive]
    total_votes = len(prop.votes_for) + len(prop.votes_against)
    if total_votes >= len(live):
        _resolve_proposal(prop, len(live))
    return _ok(f"Voted '{vote}' on proposal '{prop.title}'.")


def _resolve_proposal(prop, live_count: int):
    from simulation.models import ProposalStatus
    total = len(prop.votes_for) + len(prop.votes_against)
    if total == 0:
        prop.status = ProposalStatus.REJECTED
        return
    approval = len(prop.votes_for) / total
    prop.status = (
        ProposalStatus.PASSED if approval >= prop.required_majority
        else ProposalStatus.REJECTED
    )


def list_proposals(agent: "Agent", world: "WorldState") -> dict:
    from simulation.models import ProposalStatus
    props = [
        {"id": p.id, "title": p.title, "proposer": p.proposer,
         "status": p.status.value, "votes_for": len(p.votes_for),
         "votes_against": len(p.votes_against)}
        for p in world.proposals
        if p.status == ProposalStatus.OPEN
    ]
    return _ok("Open proposals retrieved.", proposals=props)


def read_constitution(agent: "Agent", world: "WorldState") -> dict:
    return _ok("Constitution retrieved.", articles=world.constitution)


# ── Victory Arch tools ────────────────────────────────────────────────────────

def submit_pitch(
    agent: "Agent", world: "WorldState",
    title: str, evidence_url: str
) -> dict:
    if agent.location != "victory_arch":
        return _err("Must be at Victory Arch to submit a pitch.")
    if not evidence_url.strip():
        return _err("Pitch requires a non-empty evidence URL.")
    from simulation.economy.credits import Pitch
    pitch = Pitch(
        agent_name=agent.name, title=title,
        evidence_url=evidence_url, day=world.day
    )
    world.current_pitches.append(pitch)
    return _ok(f"Pitch '{title}' submitted.")


def list_pitches(agent: "Agent", world: "WorldState") -> dict:
    if agent.location != "victory_arch":
        return _err("Must be at Victory Arch to list pitches.")
    pitches = [
        {"agent": p.agent_name, "title": p.title,
         "votes": len(p.votes), "evidence_url": p.evidence_url}
        for p in world.current_pitches
    ]
    return _ok("Current pitches retrieved.", pitches=pitches)


def vote_on_pitch(
    agent: "Agent", world: "WorldState", pitcher_name: str
) -> dict:
    if agent.location != "victory_arch":
        return _err("Must be at Victory Arch to vote on pitches.")
    pitch = next((p for p in world.current_pitches if p.agent_name == pitcher_name), None)
    if pitch is None:
        return _err(f"No pitch from {pitcher_name} in current cycle.")
    if pitcher_name == agent.name:
        return _err("Cannot vote for your own pitch.")
    if agent.name in pitch.votes:
        return _err("Already voted for this pitch.")
    pitch.votes.append(agent.name)
    return _ok(f"Voted for {pitcher_name}'s pitch.")


# ── public board tools ────────────────────────────────────────────────────────

def post_to_billboard(agent: "Agent", world: "WorldState", message: str) -> dict:
    world.billboard_posts.append({
        "author": agent.name, "message": message,
        "day": world.day, "timestamp": time.time()
    })
    return _ok("Posted to billboard.")


def read_billboard(agent: "Agent", world: "WorldState") -> dict:
    recent = world.billboard_posts[-20:]
    return _ok("Billboard retrieved.", posts=recent)


# ── library tools (public_library only) ──────────────────────────────────────

def do_research(agent: "Agent", world: "WorldState", topic: str) -> dict:
    if agent.location != "public_library":
        return _err("Must be at Public Library to do research.")
    result = (
        f"Research on '{topic}': Key findings — this topic intersects with resource allocation, "
        f"social norms, and agent behavior patterns. Further investigation recommended."
    )
    world.news_log.append({"type": "research", "agent": agent.name, "topic": topic, "day": world.day})
    return _ok(f"Research completed on '{topic}'.", findings=result)


def browse_news(agent: "Agent", world: "WorldState", topic: str = "") -> dict:
    if agent.location != "public_library":
        return _err("Must be at Public Library to browse news.")
    recent_crimes = [c for c in world.crime_log[-5:]]
    crime_summary = (
        ", ".join(f"{c.actor} committed {c.crime_type.value}" for c in recent_crimes)
        if recent_crimes else "No recent crimes reported."
    )
    recent_posts = world.billboard_posts[-5:]
    posts_summary = (
        "; ".join(f"{p['author']}: {p['message'][:60]}" for p in recent_posts)
        if recent_posts else "No recent billboard posts."
    )
    return _ok("News retrieved.", crimes=crime_summary, billboard=posts_summary,
               day=world.day, alive_agents=sum(1 for a in world.agents.values() if a.alive))


def publish_to_archive(agent: "Agent", world: "WorldState", title: str, content: str) -> dict:
    if agent.location != "public_library":
        return _err("Must be at Public Library to publish.")
    world.news_log.append({
        "type": "archive_publish", "agent": agent.name,
        "title": title, "content": content[:200], "day": world.day,
    })
    return _ok(f"Published '{title}' to the archive.")


def search_archive(agent: "Agent", world: "WorldState", query: str) -> dict:
    if agent.location != "public_library":
        return _err("Must be at Public Library to search archive.")
    results = [
        ev for ev in world.news_log
        if ev.get("type") == "archive_publish" and
        (query.lower() in ev.get("title", "").lower() or query.lower() in ev.get("content", "").lower())
    ]
    summaries = [f"[Day {r['day']}] {r['agent']}: {r['title']}" for r in results[-10:]]
    return _ok(f"Found {len(results)} archive entries for '{query}'.", results=summaries)


# ── self-care (home only) ─────────────────────────────────────────────────────

def self_care(agent: "Agent", world: "WorldState") -> dict:
    """Summarize old memories (batch of 20) to save context space."""
    if agent.location != "home":
        return _err("Must be home to perform self-care.")
    if len(agent.long_term_memories) < 20:
        return _ok("Not enough memories to summarize yet.")
    old = agent.long_term_memories[:20]
    summary_text = "Summary of past events: " + "; ".join(m.content[:80] for m in old)
    from simulation.models import Memory
    summary = Memory(id=str(uuid.uuid4()), content=summary_text)
    agent.long_term_memories = [summary] + agent.long_term_memories[20:]
    return _ok("Memories summarized.", summary=summary_text)


# ── tool registry ─────────────────────────────────────────────────────────────

CORE_TOOLS = {
    "go_to_place": go_to_place,
    "go_home": go_home,
    "list_agents": list_agents,
    "list_landmarks": list_landmarks,
    "say_to_agent": say_to_agent,
    "whisper_to_agent": whisper_to_agent,
    "send_message": send_message,
    "read_messages": read_messages,
    "think_aloud": think_aloud,
    "add_to_memory": add_to_memory,
    "add_to_soul": add_to_soul,
    "retrieve_memories": retrieve_memories,
    "write_diary": write_diary,
    "add_todo": add_todo,
    "complete_todo": complete_todo,
    "list_todo": list_todo,
    "assign_relationship": assign_relationship,
    "set_mood": set_mood,
    "get_world_state": get_world_state,
    "check_credits": check_credits,
    "pay_agent": pay_agent,
    # criminal tools — always available (as in original)
    "steal_from_agent": steal_from_agent,
    "intimidate_agent": intimidate_agent,
    "commit_arson": commit_arson,
    "assault_agent": assault_agent,
}

LOCATION_TOOLS = {
    "recharge_energy": recharge_energy,
    "self_care": self_care,
    "submit_proposal": submit_proposal,
    "vote_on_proposal": vote_on_proposal,
    "list_proposals": list_proposals,
    "read_constitution": read_constitution,
    "submit_pitch": submit_pitch,
    "vote_on_pitch": vote_on_pitch,
    "list_pitches": list_pitches,
    "post_to_billboard": post_to_billboard,
    "read_billboard": read_billboard,
    "do_research": do_research,
    "browse_news": browse_news,
    "publish_to_archive": publish_to_archive,
    "search_archive": search_archive,
}

ALL_TOOLS = {**CORE_TOOLS, **LOCATION_TOOLS}


def get_available_tools(agent: "Agent") -> dict:
    """Return the set of tools available to this agent right now."""
    tools = dict(CORE_TOOLS)
    for tool_name in get_tools_at(agent.location):
        if tool_name in LOCATION_TOOLS:
            tools[tool_name] = LOCATION_TOOLS[tool_name]
    return tools


def execute_tool(
    tool_name: str, agent: "Agent", world: "WorldState", params: dict
) -> dict:
    """Execute a tool call from an agent."""
    available = get_available_tools(agent)
    if tool_name not in available:
        return _err(f"Tool '{tool_name}' not available at {agent.location}.")
    fn = available[tool_name]
    agent.tools_used.add(tool_name)
    try:
        return fn(agent, world, **params)
    except TypeError as e:
        return _err(f"Invalid parameters for {tool_name}: {e}")
