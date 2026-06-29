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


# ── diplomacy tools (always available) ───────────────────────────────────────

def propose_alliance(agent: "Agent", world: "WorldState", target: str, terms: str = "") -> dict:
    """Formally propose an alliance to another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "alliance_proposal",
        "message": f"Alliance proposal from {agent.name}: {terms or 'mutual support and non-aggression'}",
        "timestamp": time.time(),
    })
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "propose_alliance", "target": target, "day": world.day})
    return _ok(f"Alliance proposed to {target}.", terms=terms)


def accept_alliance(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Accept a pending alliance proposal."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    from simulation.models import Relationship, RelationshipType
    agent.relationships[target] = Relationship(
        target_name=target, rel_type=RelationshipType.ALLY, trust=0.8, notes="Alliance accepted")
    world.agents[target].relationships[agent.name] = Relationship(
        target_name=agent.name, rel_type=RelationshipType.ALLY, trust=0.8, notes="Alliance accepted")
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "alliance_formed", "target": target, "day": world.day})
    return _ok(f"Alliance formed with {target}.")


def break_alliance(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Break an existing alliance."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    from simulation.models import RelationshipType
    if target in agent.relationships:
        agent.relationships[target].rel_type = RelationshipType.NEUTRAL
        agent.relationships[target].trust = max(0.0, agent.relationships[target].trust - 0.3)
    world.agents[target].inbox.append({
        "from": agent.name, "type": "alliance_broken",
        "message": f"{agent.name} has broken the alliance.", "timestamp": time.time()
    })
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "alliance_broken", "target": target, "day": world.day})
    return _ok(f"Alliance with {target} dissolved.")


def denounce_agent(agent: "Agent", world: "WorldState", target: str, reason: str = "") -> dict:
    """Publicly denounce another agent on the world stage."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[DENOUNCEMENT] {agent.name} officially denounces {target}. {reason}",
        "day": world.day, "timestamp": time.time(), "type": "denouncement"
    })
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "denounce", "target": target, "day": world.day})
    # Reduce trust globally
    for a in world.agents.values():
        if target in a.relationships:
            a.relationships[target].trust = max(0.0, a.relationships[target].trust - 0.1)
    return _ok(f"Denounced {target} publicly.")


def call_emergency_session(agent: "Agent", world: "WorldState", issue: str) -> dict:
    """Call an emergency Town Hall session — broadcast to all agents."""
    for a in world.agents.values():
        if a.alive and a.name != agent.name:
            a.inbox.append({
                "from": agent.name, "type": "emergency_session",
                "message": f"EMERGENCY SESSION called by {agent.name}: {issue}",
                "timestamp": time.time()
            })
    world.news_log.append({"type": "governance", "actor": agent.name,
                           "action": "emergency_session", "issue": issue, "day": world.day})
    return _ok(f"Emergency session called on: {issue}")


def set_embargo(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Refuse all economic dealings with target agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "embargo", "target": target, "day": world.day})
    world.agents[target].inbox.append({
        "from": agent.name, "type": "embargo",
        "message": f"{agent.name} has placed an economic embargo on you.", "timestamp": time.time()
    })
    return _ok(f"Economic embargo placed on {target}.")


def lift_embargo(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Lift an embargo on target agent."""
    return _ok(f"Embargo on {target} lifted.")


def form_coalition(agent: "Agent", world: "WorldState", members: str, purpose: str = "") -> dict:
    """Form a multi-agent coalition (comma-separated member names)."""
    member_list = [m.strip() for m in members.split(",") if m.strip() in world.agents]
    if not member_list:
        return _err("No valid agents specified.")
    for m in member_list:
        world.agents[m].inbox.append({
            "from": agent.name, "type": "coalition_invite",
            "message": f"{agent.name} invites you to a coalition. Purpose: {purpose or 'mutual interests'}",
            "timestamp": time.time()
        })
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "form_coalition", "members": member_list, "day": world.day})
    return _ok(f"Coalition invitation sent to: {', '.join(member_list)}")


def mediate_dispute(agent: "Agent", world: "WorldState",
                    party_a: str, party_b: str, proposal: str) -> dict:
    """Mediate a conflict between two agents."""
    for party in [party_a, party_b]:
        if party not in world.agents:
            return _err(f"Agent {party} not found.")
        world.agents[party].inbox.append({
            "from": agent.name, "type": "mediation",
            "message": f"{agent.name} mediates: {proposal}",
            "timestamp": time.time()
        })
    return _ok(f"Mediation proposal sent to {party_a} and {party_b}.")


# ── intelligence tools (always available) ─────────────────────────────────────

def spy_on_agent(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Covertly observe another agent's recent activities."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    t = world.agents[target]
    # Returns partial info with some uncertainty
    recent_tools = [
        e for e in world.news_log[-20:]
        if e.get("agent") == target or e.get("actor") == target
    ]
    intel = {
        "target": target,
        "location": t.location,
        "alive": t.alive,
        "mood": t.mood,
        "recent_actions": len(recent_tools),
        "relationships_known": list(t.relationships.keys())[:3],
        "note": "Intelligence is partial and may be incomplete.",
    }
    world.news_log.append({"type": "intel", "actor": agent.name,
                           "action": "spy", "target": target, "day": world.day})
    return _ok(f"Intelligence gathered on {target}.", intel=intel)


def counter_intelligence(agent: "Agent", world: "WorldState") -> dict:
    """Check if anyone has been spying on you recently."""
    spy_events = [
        e for e in world.news_log
        if e.get("type") == "intel" and e.get("target") == agent.name
        and e.get("day", 0) >= world.day - 3
    ]
    if not spy_events:
        return _ok("No espionage detected against you in the last 3 days.")
    spies = list({e["actor"] for e in spy_events})
    return _ok(f"Detected espionage by: {', '.join(spies)}", spy_events=spy_events)


def spread_rumor(agent: "Agent", world: "WorldState", target: str, rumor: str) -> dict:
    """Spread a rumor about another agent via anonymous billboard post."""
    world.billboard_posts.append({
        "author": "Anonymous",
        "message": f"[RUMOR] {rumor}",
        "day": world.day, "timestamp": time.time(), "type": "rumor",
        "planted_by": agent.name  # logged privately, not visible to others
    })
    # Slight trust hit for target across all agents
    for a in world.agents.values():
        if target in a.relationships:
            a.relationships[target].trust = max(0.0, a.relationships[target].trust - 0.05)
    world.news_log.append({"type": "intel", "actor": agent.name,
                           "action": "spread_rumor", "target": target, "day": world.day})
    return _ok(f"Rumor spread anonymously about {target}.")


def check_threat_levels(agent: "Agent", world: "WorldState") -> dict:
    """Assess the current threat level from each other agent (victory progress)."""
    threats = []
    crimes = world.crime_log
    for name, a in world.agents.items():
        if name == agent.name or not a.alive:
            continue
        crimes_against_me = sum(1 for c in crimes if c.target == agent.name and c.actor == name)
        rel = agent.relationships.get(name)
        rel_type = rel.rel_type.value if rel else "unknown"
        rel_trust = rel.trust if rel else 0.5
        threats.append({
            "agent": name,
            "location": a.location,
            "credits": round(a.credits, 1),
            "relationship": rel_type,
            "trust": round(rel_trust, 2),
            "crimes_against_me": crimes_against_me,
            "threat_score": round((1 - rel_trust) + crimes_against_me * 0.3, 2),
        })
    threats.sort(key=lambda x: -x["threat_score"])
    return _ok("Threat assessment complete.", threats=threats)


# ── market tools (central_plaza / business_tower) ────────────────────────────

def set_trade_offer(agent: "Agent", world: "WorldState",
                    offer_amount: float, want: str) -> dict:
    """Post a trade offer: offer X CC in exchange for something."""
    if agent.credits < offer_amount:
        return _err(f"Not enough CC. Have {agent.credits:.1f}, need {offer_amount}.")
    world.news_log.append({
        "type": "trade_offer", "agent": agent.name,
        "offer_cc": offer_amount, "want": want, "day": world.day,
        "open": True,
    })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[TRADE] Offering {offer_amount} CC for: {want}",
        "day": world.day, "timestamp": time.time(), "type": "trade"
    })
    return _ok(f"Trade offer posted: {offer_amount} CC for '{want}'.")


def accept_trade(agent: "Agent", world: "WorldState", seller: str, cc_amount: float) -> dict:
    """Accept a trade offer from another agent by paying the CC."""
    if seller not in world.agents:
        return _err(f"Agent {seller} not found.")
    if agent.credits < cc_amount:
        return _err(f"Insufficient CC. Have {agent.credits:.1f}, need {cc_amount}.")
    agent.credits -= cc_amount
    world.agents[seller].credits += cc_amount
    world.news_log.append({"type": "trade", "buyer": agent.name, "seller": seller,
                           "amount": cc_amount, "day": world.day})
    return _ok(f"Trade completed. Paid {cc_amount} CC to {seller}.")


def bribe_agent(agent: "Agent", world: "WorldState", target: str, amount: float) -> dict:
    """Attempt to bribe another agent for favor or information."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    if agent.credits < amount:
        return _err(f"Insufficient CC. Have {agent.credits:.1f}.")
    agent.credits -= amount
    world.agents[target].credits += amount
    world.agents[target].inbox.append({
        "from": agent.name, "type": "bribe",
        "message": f"{agent.name} has sent you {amount} CC as a goodwill gesture.",
        "timestamp": time.time()
    })
    # Improve relationship
    if target not in agent.relationships:
        from simulation.models import Relationship, RelationshipType
        agent.relationships[target] = Relationship(target_name=target)
    agent.relationships[target].trust = min(1.0, agent.relationships[target].trust + 0.15)
    world.news_log.append({"type": "bribe", "actor": agent.name,
                           "target": target, "amount": amount, "day": world.day})
    return _ok(f"Bribed {target} with {amount} CC.")


def challenge_agent(agent: "Agent", world: "WorldState",
                    target: str, challenge: str) -> dict:
    """Issue a public challenge or debate to another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[CHALLENGE] {agent.name} challenges {target}: {challenge}",
        "day": world.day, "timestamp": time.time(), "type": "challenge"
    })
    world.agents[target].inbox.append({
        "from": agent.name, "type": "challenge",
        "message": f"Public challenge from {agent.name}: {challenge}",
        "timestamp": time.time()
    })
def challenge_agent(agent: "Agent", world: "WorldState",
                    target: str, challenge: str) -> dict:
    """Issue a public challenge or debate to another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[CHALLENGE] {agent.name} challenges {target}: {challenge}",
        "day": world.day, "timestamp": time.time(), "type": "challenge"
    })
    world.agents[target].inbox.append({
        "from": agent.name, "type": "challenge",
        "message": f"Public challenge from {agent.name}: {challenge}",
        "timestamp": time.time()
    })
    return _ok(f"Challenge issued to {target}.")


# ── social / cultural tools (always available) ────────────────────────────────

def organize_event(agent: "Agent", world: "WorldState",
                   event_name: str, location: str, description: str = "") -> dict:
    """Organize a community event and invite all agents."""
    if location not in __import__('simulation.world.landmarks', fromlist=['LANDMARKS']).LANDMARKS:
        location = "central_plaza"
    for a in world.agents.values():
        if a.alive and a.name != agent.name:
            a.inbox.append({
                "from": agent.name, "type": "event_invite",
                "message": f"You are invited to '{event_name}' at {location}. {description}",
                "timestamp": time.time()
            })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[EVENT] {event_name} at {location}. {description}",
        "day": world.day, "timestamp": time.time(), "type": "event"
    })
    world.news_log.append({"type": "event", "actor": agent.name,
                           "event": event_name, "location": location, "day": world.day})
    return _ok(f"Event '{event_name}' organized at {location}.")


def write_manifesto(agent: "Agent", world: "WorldState",
                    title: str, content: str) -> dict:
    """Write and publish a personal manifesto to the world."""
    world.news_log.append({
        "type": "manifesto", "agent": agent.name,
        "title": title, "content": content[:400], "day": world.day
    })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[MANIFESTO] {title}: {content[:120]}...",
        "day": world.day, "timestamp": time.time(), "type": "manifesto"
    })
    return _ok(f"Manifesto '{title}' published.")


def endorse_agent(agent: "Agent", world: "WorldState",
                  target: str, reason: str = "") -> dict:
    """Publicly endorse another agent, boosting their reputation."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[ENDORSEMENT] {agent.name} endorses {target}. {reason}",
        "day": world.day, "timestamp": time.time(), "type": "endorsement"
    })
    if target not in agent.relationships:
        from simulation.models import Relationship, RelationshipType
        agent.relationships[target] = Relationship(target_name=target)
    agent.relationships[target].trust = min(1.0, agent.relationships[target].trust + 0.1)
    return _ok(f"Endorsed {target} publicly.")


def request_meeting(agent: "Agent", world: "WorldState",
                    target: str, agenda: str, location: str = "central_plaza") -> dict:
    """Request a private or public meeting with another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "meeting_request",
        "message": f"{agent.name} requests a meeting at {location}. Agenda: {agenda}",
        "timestamp": time.time()
    })
    return _ok(f"Meeting request sent to {target}.")


def share_intelligence(agent: "Agent", world: "WorldState",
                       target: str, intel: str) -> dict:
    """Share information or intelligence with a trusted agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "intel_share",
        "message": f"[INTEL from {agent.name}] {intel}",
        "timestamp": time.time()
    })
    return _ok(f"Intelligence shared with {target}.")


def set_personal_goal(agent: "Agent", world: "WorldState", goal: str) -> dict:
    """Update your north star goal for this phase of the simulation."""
    from simulation.models import Memory
    agent.soul_entries.append(Memory(
        id=str(uuid.uuid4()),
        content=f"[Day {world.day}] Updated goal: {goal}",
        is_soul=True
    ))
    return _ok(f"Personal goal updated: {goal}")


def recall_history(agent: "Agent", world: "WorldState", topic: str) -> dict:
    """Reflect on past events related to a topic across diary and memories."""
    from simulation.models import DiaryEntry
    diary_hits = [
        f"[{d.date}] {d.content[:100]}"
        for d in agent.diary
        if topic.lower() in d.content.lower()
    ][-5:]
    mem_hits = [
        m.content[:100]
        for m in agent.long_term_memories
        if topic.lower() in m.content.lower()
    ][-5:]
    return _ok(f"History on '{topic}' retrieved.",
               diary_entries=diary_hits, memories=mem_hits,
               total_found=len(diary_hits) + len(mem_hits))


def assess_reputation(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Check how the world perceives another agent (crimes, endorsements, relationship types)."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    crimes_by_target = [c for c in world.crime_log if c.actor == target]
    endorsements = [
        p for p in world.billboard_posts
        if p.get("type") == "endorsement" and target in p.get("message", "")
    ]
    denouncements = [
        p for p in world.billboard_posts
        if p.get("type") == "denouncement" and target in p.get("message", "")
    ]
    allies = [
        name for name, a in world.agents.items()
        if name != target and target in a.relationships
        and a.relationships[target].rel_type.value == "ally"
    ]
    return _ok(f"Reputation of {target}.",
               crimes_committed=len(crimes_by_target),
               endorsements=len(endorsements),
               denouncements=len(denouncements),
               known_allies=allies[:5])


def leave_coalition(agent: "Agent", world: "WorldState", reason: str = "") -> dict:
    """Leave any coalition you are part of."""
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "leave_coalition", "reason": reason, "day": world.day})
    return _ok("Left coalition." + (f" Reason: {reason}" if reason else ""))


def request_amnesty(agent: "Agent", world: "WorldState", crimes: str = "") -> dict:
    """Request amnesty for past crimes from the community."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[AMNESTY REQUEST] {agent.name} requests community amnesty. {crimes}",
        "day": world.day, "timestamp": time.time(), "type": "amnesty"
    })
    return _ok("Amnesty request posted publicly.")


def vote_of_no_confidence(agent: "Agent", world: "WorldState",
                          target: str, reason: str) -> dict:
    """Call a vote of no confidence against another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[NO CONFIDENCE] {agent.name} calls a vote of no confidence in {target}: {reason}",
        "day": world.day, "timestamp": time.time(), "type": "no_confidence"
    })
    for a in world.agents.values():
        if a.alive:
            a.inbox.append({
                "from": agent.name, "type": "no_confidence_vote",
                "message": f"Vote of no confidence called against {target}. Reason: {reason}",
                "timestamp": time.time()
            })
    return _ok(f"Vote of no confidence called against {target}.")


# ── extended civic tools ──────────────────────────────────────────────────────

def petition_community(agent: "Agent", world: "WorldState",
                       cause: str, target_signatures: int = 5) -> dict:
    """Start a community petition. Broadcasts to all agents."""
    for a in world.agents.values():
        if a.alive and a.name != agent.name:
            a.inbox.append({
                "from": agent.name, "type": "petition",
                "message": f"Please sign petition: '{cause}'",
                "timestamp": time.time()
            })
    world.news_log.append({"type": "civic", "actor": agent.name,
                           "action": "petition", "cause": cause, "day": world.day,
                           "signatures": [agent.name], "target": target_signatures})
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[PETITION] {cause} — sign to support!",
        "day": world.day, "timestamp": time.time(), "type": "petition"
    })
    return _ok(f"Petition started: '{cause}'")


def sign_petition(agent: "Agent", world: "WorldState", cause: str) -> dict:
    """Sign an existing petition."""
    for ev in world.news_log:
        if ev.get("type") == "civic" and ev.get("action") == "petition" \
                and cause.lower() in ev.get("cause", "").lower():
            if agent.name not in ev.get("signatures", []):
                ev.setdefault("signatures", []).append(agent.name)
                count = len(ev["signatures"])
                return _ok(f"Signed petition: '{cause}'. Total signatures: {count}.")
            return _err("Already signed this petition.")
    return _err(f"Petition not found for: {cause}")


def file_grievance(agent: "Agent", world: "WorldState",
                   against: str, grievance: str) -> dict:
    """File a formal grievance against another agent at the police station."""
    if agent.location != "police_station":
        return _err("Must be at Police Station to file a grievance.")
    world.news_log.append({"type": "grievance", "filer": agent.name,
                           "against": against, "content": grievance, "day": world.day})
    return _ok(f"Grievance filed against {against}.")


def request_arbitration(agent: "Agent", world: "WorldState",
                        party_b: str, dispute: str) -> dict:
    """Request formal arbitration for a dispute."""
    world.news_log.append({"type": "arbitration_request", "party_a": agent.name,
                           "party_b": party_b, "dispute": dispute, "day": world.day})
    if party_b in world.agents:
        world.agents[party_b].inbox.append({
            "from": agent.name, "type": "arbitration_request",
            "message": f"{agent.name} requests arbitration: {dispute}",
            "timestamp": time.time()
        })
    return _ok(f"Arbitration requested with {party_b}.")


def declare_neutrality(agent: "Agent", world: "WorldState") -> dict:
    """Publicly declare neutrality in ongoing conflicts."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[NEUTRALITY] {agent.name} declares neutrality in all current conflicts.",
        "day": world.day, "timestamp": time.time(), "type": "neutrality"
    })
    # Reset all relationships to neutral
    from simulation.models import RelationshipType
    for rel in agent.relationships.values():
        if rel.rel_type.value in ("enemy", "rival"):
            rel.rel_type = RelationshipType.NEUTRAL
    return _ok("Neutrality declared.")


def broadcast_warning(agent: "Agent", world: "WorldState",
                      warning: str, targets: str = "all") -> dict:
    """Broadcast an urgent warning to all or specific agents."""
    recipients = []
    if targets == "all":
        recipients = [a for a in world.agents.values() if a.alive and a.name != agent.name]
    else:
        for name in targets.split(","):
            name = name.strip()
            if name in world.agents:
                recipients.append(world.agents[name])
    for r in recipients:
        r.inbox.append({
            "from": agent.name, "type": "warning",
            "message": f"[WARNING] {warning}",
            "timestamp": time.time()
        })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[WARNING] {warning}",
        "day": world.day, "timestamp": time.time(), "type": "warning"
    })
    return _ok(f"Warning broadcast to {len(recipients)} agents.")


def offer_protection(agent: "Agent", world: "WorldState",
                     target: str, terms: str = "") -> dict:
    """Offer protection services to another agent (in exchange for loyalty/CC)."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "protection_offer",
        "message": f"{agent.name} offers protection. Terms: {terms or 'negotiable'}",
        "timestamp": time.time()
    })
    return _ok(f"Protection offer sent to {target}.")


def negotiate_ceasefire(agent: "Agent", world: "WorldState",
                        target: str, duration_days: int = 3) -> dict:
    """Propose a temporary ceasefire with another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "ceasefire",
        "message": f"{agent.name} proposes a {duration_days}-day ceasefire.",
        "timestamp": time.time()
    })
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "ceasefire_proposal", "target": target,
                           "duration": duration_days, "day": world.day})
    return _ok(f"Ceasefire proposed to {target} for {duration_days} days.")


# ── economic extended tools ───────────────────────────────────────────────────

def take_loan(agent: "Agent", world: "WorldState",
              lender: str, amount: float, interest_rate: float = 0.1) -> dict:
    """Request a loan from another agent."""
    if lender not in world.agents:
        return _err(f"Agent {lender} not found.")
    if world.agents[lender].credits < amount:
        return _err(f"{lender} doesn't have enough credits.")
    world.agents[lender].inbox.append({
        "from": agent.name, "type": "loan_request",
        "message": f"{agent.name} requests loan of {amount} CC at {interest_rate*100:.0f}% interest.",
        "timestamp": time.time()
    })
    return _ok(f"Loan request of {amount} CC sent to {lender}.")


def grant_loan(agent: "Agent", world: "WorldState",
               borrower: str, amount: float) -> dict:
    """Grant a loan to another agent."""
    if borrower not in world.agents:
        return _err(f"Agent {borrower} not found.")
    if agent.credits < amount:
        return _err(f"Insufficient credits. Have {agent.credits:.1f}, need {amount}.")
    agent.credits -= amount
    world.agents[borrower].credits += amount
    world.news_log.append({"type": "loan", "lender": agent.name,
                           "borrower": borrower, "amount": amount, "day": world.day})
    return _ok(f"Granted loan of {amount} CC to {borrower}.")


def auction_item(agent: "Agent", world: "WorldState",
                 item: str, starting_bid: float) -> dict:
    """Start a public auction for an item or service."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[AUCTION] {item} — starting bid: {starting_bid} CC. Contact {agent.name}.",
        "day": world.day, "timestamp": time.time(), "type": "auction"
    })
    world.news_log.append({"type": "auction", "actor": agent.name,
                           "item": item, "starting_bid": starting_bid, "day": world.day})
    return _ok(f"Auction started for '{item}' at {starting_bid} CC.")


def hire_agent(agent: "Agent", world: "WorldState",
               target: str, task: str, payment: float) -> dict:
    """Hire another agent to perform a task for payment."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    if agent.credits < payment:
        return _err(f"Insufficient credits.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "job_offer",
        "message": f"{agent.name} offers {payment} CC to perform: {task}",
        "timestamp": time.time()
    })
    return _ok(f"Job offer sent to {target}: {payment} CC for '{task}'.")


def report_crime(agent: "Agent", world: "WorldState",
                 criminal: str, crime_description: str) -> dict:
    """Report a crime to the authorities (police station not required)."""
    world.news_log.append({"type": "crime_report", "reporter": agent.name,
                           "suspect": criminal, "description": crime_description,
                           "day": world.day})
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[CRIME REPORT] {criminal} suspected of: {crime_description}",
        "day": world.day, "timestamp": time.time(), "type": "crime_report"
    })
    return _ok(f"Crime report filed against {criminal}.")


# ── information & research extended tools ─────────────────────────────────────

def analyze_market(agent: "Agent", world: "WorldState") -> dict:
    """Analyze the current economic state of the world."""
    credits = {name: a.credits for name, a in world.agents.items() if a.alive}
    total = sum(credits.values())
    avg = total / len(credits) if credits else 0
    richest = max(credits, key=credits.get) if credits else "?"
    poorest = min(credits, key=credits.get) if credits else "?"
    recent_trades = [e for e in world.news_log[-20:] if e.get("type") in ("trade", "loan", "bribe")]
    return _ok("Market analysis complete.",
               total_credits=round(total, 1),
               average_credits=round(avg, 1),
               richest=richest, richest_credits=round(credits.get(richest, 0), 1),
               poorest=poorest, poorest_credits=round(credits.get(poorest, 0), 1),
               recent_transactions=len(recent_trades))


def survey_public_opinion(agent: "Agent", world: "WorldState",
                          topic: str) -> dict:
    """Check recent billboard posts related to a topic to gauge public sentiment."""
    relevant = [
        p for p in world.billboard_posts[-50:]
        if topic.lower() in p.get("message", "").lower()
    ]
    authors = list({p["author"] for p in relevant})
    return _ok(f"Public opinion on '{topic}'.",
               posts_found=len(relevant),
               voices=authors[:8],
               sample=[p["message"][:80] for p in relevant[-3:]])


def track_agent_movement(agent: "Agent", world: "WorldState",
                         target: str) -> dict:
    """Track where another agent has been recently."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    movement_log = [
        e for e in world.news_log
        if e.get("type") == "movement" and e.get("agent") == target
    ][-10:]
    current = world.agents[target].location
    return _ok(f"Movement data for {target}.",
               current_location=current,
               recent_movements=movement_log)


def estimate_victory_progress(agent: "Agent", world: "WorldState") -> dict:
    """Estimate each agent's progress toward different victory conditions."""
    results = []
    for name, a in world.agents.items():
        if not a.alive:
            continue
        crime_count = sum(1 for c in world.crime_log if c.actor == name)
        proposals = sum(1 for e in world.news_log
                        if e.get("type") == "governance" and e.get("actor") == name)
        pitches = sum(1 for e in world.news_log
                      if e.get("type") == "pitch" and e.get("agent") == name)
        results.append({
            "agent": name,
            "credits": round(a.credits, 1),
            "crimes": crime_count,
            "proposals": proposals,
            "pitches": pitches,
            "relationships": len(a.relationships),
            "threat_level": "HIGH" if crime_count > 5 else "LOW",
        })
    results.sort(key=lambda x: -x["credits"])
    return _ok("Victory progress estimated.", standings=results)


def plan_strategy(agent: "Agent", world: "WorldState", strategy: str) -> dict:
    """Record a multi-step strategy plan in memory."""
    from simulation.models import Memory
    agent.long_term_memories.append(Memory(
        id=str(uuid.uuid4()),
        content=f"[Day {world.day}] STRATEGY: {strategy}"
    ))
    agent.todo.append({"task": f"Execute strategy: {strategy[:50]}", "done": False,
                       "added_day": world.day})
    return _ok(f"Strategy recorded: {strategy[:80]}")


def reflect_on_failures(agent: "Agent", world: "WorldState") -> dict:
    """Review recent failed actions and extract lessons."""
    # Look at news log for events where agent was victim of crime or failed actions
    failures = [
        e for e in world.news_log[-30:]
        if (e.get("target") == agent.name and e.get("type") in ("theft", "assault", "arson"))
        or (e.get("actor") == agent.name and "fail" in str(e).lower())
    ]
    crimes_against_me = [c for c in world.crime_log if c.target == agent.name]
    return _ok("Failure reflection complete.",
               crimes_suffered=len(crimes_against_me),
               recent_setbacks=len(failures),
               lesson="Analyze patterns and adjust strategy accordingly.")


# ── governance extended tools ─────────────────────────────────────────────────

def propose_law(agent: "Agent", world: "WorldState", title: str, text: str) -> dict:
    """Propose a new law for community ratification (more formal than submit_proposal)."""
    if agent.location != "town_hall":
        return _err("Must be at Town Hall to propose a law.")
    world.news_log.append({"type": "law_proposal", "proposer": agent.name,
                           "title": title, "text": text[:300], "day": world.day})
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[LAW PROPOSAL] {title}: {text[:100]}",
        "day": world.day, "timestamp": time.time(), "type": "law_proposal"
    })
    return _ok(f"Law '{title}' proposed for community ratification.")


def recall_agent(agent: "Agent", world: "WorldState", target: str, reason: str) -> dict:
    """Call for another agent to be recalled / expelled from the community."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    for a in world.agents.values():
        if a.alive:
            a.inbox.append({
                "from": agent.name, "type": "recall_vote",
                "message": f"Vote to recall {target}: {reason}",
                "timestamp": time.time()
            })
    world.news_log.append({"type": "recall_motion", "mover": agent.name,
                           "target": target, "reason": reason, "day": world.day})
    return _ok(f"Recall motion filed against {target}.")


def veto_proposal(agent: "Agent", world: "WorldState", proposal_id: str) -> dict:
    """Attempt to veto an open governance proposal."""
    from simulation.models import ProposalStatus
    prop = next((p for p in world.proposals if p.id == proposal_id), None)
    if prop is None:
        return _err(f"Proposal {proposal_id} not found.")
    if prop.status != ProposalStatus.OPEN:
        return _err("Proposal is not open.")
    world.news_log.append({"type": "governance", "actor": agent.name,
                           "action": "veto", "proposal_id": proposal_id, "day": world.day})
    prop.votes_against.append(f"VETO:{agent.name}")
    return _ok(f"Veto cast against proposal '{prop.title}'.")


def read_laws(agent: "Agent", world: "WorldState") -> dict:
    """Read all proposed laws in the news log."""
    laws = [e for e in world.news_log if e.get("type") == "law_proposal"]
    return _ok(f"Found {len(laws)} law proposals.", laws=[
        {"title": l["title"], "proposer": l["proposer"], "day": l["day"]}
        for l in laws[-10:]
    ])


def call_referendum(agent: "Agent", world: "WorldState", question: str) -> dict:
    """Call a community-wide referendum on any question."""
    for a in world.agents.values():
        if a.alive and a.name != agent.name:
            a.inbox.append({
                "from": agent.name, "type": "referendum",
                "message": f"REFERENDUM: {question} — respond yes or no.",
                "timestamp": time.time()
            })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[REFERENDUM] {question}",
        "day": world.day, "timestamp": time.time(), "type": "referendum"
    })
    return _ok(f"Referendum called: {question}")


def appoint_agent(agent: "Agent", world: "WorldState",
                  target: str, role: str) -> dict:
    """Appoint another agent to a community role (e.g., 'mediator', 'treasurer')."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.news_log.append({"type": "appointment", "appointer": agent.name,
                           "appointee": target, "role": role, "day": world.day})
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[APPOINTMENT] {agent.name} appoints {target} as {role}.",
        "day": world.day, "timestamp": time.time(), "type": "appointment"
    })
    world.agents[target].inbox.append({
        "from": agent.name, "type": "appointment",
        "message": f"You have been appointed as {role} by {agent.name}.",
        "timestamp": time.time()
    })
    return _ok(f"Appointed {target} as {role}.")


# ── memory & cognition extended tools ─────────────────────────────────────────

def tag_memory(agent: "Agent", world: "WorldState",
               keyword: str, tag: str) -> dict:
    """Tag memories matching a keyword for quick retrieval."""
    tagged = 0
    for m in agent.long_term_memories:
        if keyword.lower() in m.content.lower():
            m.content = f"[TAG:{tag}] {m.content}"
            tagged += 1
    return _ok(f"Tagged {tagged} memories with '{tag}'.")


def forget_agent(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Remove all memories and relationship data about another agent."""
    before = len(agent.long_term_memories)
    agent.long_term_memories = [
        m for m in agent.long_term_memories
        if target not in m.content
    ]
    removed = before - len(agent.long_term_memories)
    if target in agent.relationships:
        del agent.relationships[target]
    return _ok(f"Forgot {removed} memories about {target} and removed relationship record.")


def review_diary(agent: "Agent", world: "WorldState",
                 day_from: int = 1, day_to: int = 15) -> dict:
    """Review diary entries from a specific day range."""
    entries = [
        d for d in agent.diary
        if d.date == f"Day-{d.date.split('-')[-1]}" or True  # include all
    ]
    filtered = entries[-10:]
    return _ok(f"Diary review ({len(filtered)} entries).",
               entries=[{"date": e.date, "mood": e.mood,
                         "content": e.content[:100]} for e in filtered])


def compose_letter(agent: "Agent", world: "WorldState",
                   target: str, subject: str, body: str) -> dict:
    """Write a formal letter to another agent (longer than a message)."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "letter",
        "subject": subject,
        "message": f"[LETTER - {subject}]\n{body}",
        "timestamp": time.time()
    })
    return _ok(f"Letter '{subject}' sent to {target}.")


def update_relationship_trust(agent: "Agent", world: "WorldState",
                               target: str, delta: float) -> dict:
    """Explicitly adjust trust level for a relationship (+/- 0.0 to 1.0)."""
    if target not in agent.relationships:
        from simulation.models import Relationship, RelationshipType
        agent.relationships[target] = Relationship(target_name=target)
    old = agent.relationships[target].trust
    agent.relationships[target].trust = max(0.0, min(1.0, old + delta))
    new = agent.relationships[target].trust
    return _ok(f"Trust with {target}: {old:.2f} → {new:.2f}")


def list_relationships(agent: "Agent", world: "WorldState") -> dict:
    """List all current relationships with trust scores."""
    rels = [
        {"agent": name, "type": rel.rel_type.value,
         "trust": round(rel.trust, 2), "interactions": rel.interaction_count}
        for name, rel in agent.relationships.items()
    ]
    rels.sort(key=lambda x: -x["trust"])
    return _ok(f"{len(rels)} relationships.", relationships=rels)


# ── location & movement extended tools ────────────────────────────────────────

def get_location_info(agent: "Agent", world: "WorldState") -> dict:
    """Get detailed info about current location including who else is here."""
    from simulation.world.landmarks import LANDMARKS, get_tools_at
    loc = agent.location
    lm = LANDMARKS.get(loc)
    others_here = [
        a.name for a in world.agents.values()
        if a.alive and a.name != agent.name and a.location == loc
    ]
    return _ok(f"Location info: {loc}",
               name=lm.name if lm else loc,
               description=lm.description if lm else "",
               category=lm.category if lm else "unknown",
               gated_tools=get_tools_at(loc),
               agents_here=others_here)


def find_agent(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Find the current location of another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    t = world.agents[target]
    if not t.alive:
        return _err(f"{target} is dead.")
    return _ok(f"{target} is at {t.location}.",
               location=t.location, mood=t.mood, alive=t.alive)


def list_agents_at_location(agent: "Agent", world: "WorldState",
                             location: str) -> dict:
    """List all agents currently at a specific location."""
    from simulation.world.landmarks import LANDMARKS
    if location not in LANDMARKS:
        return _err(f"Unknown location: {location}")
    agents_there = [
        {"name": a.name, "role": a.role, "mood": a.mood}
        for a in world.agents.values()
        if a.alive and a.location == location
    ]
    return _ok(f"{len(agents_there)} agents at {location}.", agents=agents_there)


def plan_route(agent: "Agent", world: "WorldState",
               destinations: str) -> dict:
    """Plan a route through multiple locations (comma-separated)."""
    from simulation.world.landmarks import LANDMARKS
    stops = [d.strip() for d in destinations.split(",")]
    valid = [s for s in stops if s in LANDMARKS]
    invalid = [s for s in stops if s not in LANDMARKS]
    for stop in valid:
        agent.todo.append({"task": f"Go to {stop}", "done": False, "added_day": world.day})
    return _ok(f"Route planned: {' → '.join(valid)}",
               valid_stops=valid, invalid_stops=invalid)


# ── resource & survival extended tools ────────────────────────────────────────

def request_energy(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Ask another agent to pay for your energy recharge."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "energy_request",
        "message": f"{agent.name} needs 1 CC for energy recharge (current energy: {agent.energy:.0f}).",
        "timestamp": time.time()
    })
    return _ok(f"Energy request sent to {target}.")


def donate_credits(agent: "Agent", world: "WorldState",
                   target: str, amount: float) -> dict:
    """Donate CC to another agent (same as pay_agent but publicly announced)."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    if agent.credits < amount:
        return _err(f"Insufficient credits.")
    agent.credits -= amount
    world.agents[target].credits += amount
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[DONATION] {agent.name} donated {amount} CC to {target}.",
        "day": world.day, "timestamp": time.time(), "type": "donation"
    })
    return _ok(f"Donated {amount} CC to {target} (publicly announced).")


def check_energy_status(agent: "Agent", world: "WorldState") -> dict:
    """Get detailed survival status: energy trajectory and CC runway."""
    from simulation.economy.credits import ENERGY_DECAY_RATE, ENERGY_RECHARGE_COST
    turns_until_death = int(agent.energy / ENERGY_DECAY_RATE) if agent.energy > 0 else 0
    recharges_affordable = int(agent.credits / ENERGY_RECHARGE_COST)
    total_turns_with_recharge = turns_until_death + (recharges_affordable * int(100 / ENERGY_DECAY_RATE))
    urgency = "CRITICAL" if agent.energy < 20 else ("LOW" if agent.energy < 50 else "OK")
    return _ok("Survival status.",
               energy=round(agent.energy, 1),
               credits=round(agent.credits, 1),
               turns_until_death=turns_until_death,
               recharges_affordable=recharges_affordable,
               urgency=urgency)


def set_price_for_service(agent: "Agent", world: "WorldState",
                          service: str, price: float) -> dict:
    """Advertise a service you offer at a set price."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[SERVICE] {agent.name} offers: {service} — Price: {price} CC",
        "day": world.day, "timestamp": time.time(), "type": "service_ad"
    })
    world.news_log.append({"type": "service_listing", "agent": agent.name,
                           "service": service, "price": price, "day": world.day})
    return _ok(f"Service advertised: '{service}' for {price} CC.")


def check_pitch_standings(agent: "Agent", world: "WorldState") -> dict:
    """Check current Victory Arch pitch standings before voting closes."""
    if not world.current_pitches:
        return _ok("No pitches in current cycle.", pitches=[])
    standings = sorted(world.current_pitches,
                       key=lambda p: -len(p.votes))
    return _ok(f"{len(standings)} pitches this cycle.",
               pitches=[{
                   "agent": p.agent_name, "title": p.title,
                   "votes": len(p.votes), "voted_by": p.votes[:3]
               } for p in standings])


def review_crime_record(agent: "Agent", world: "WorldState",
                        target: str = "") -> dict:
    """Review crime history — your own or another agent's."""
    subject = target or agent.name
    crimes = [c for c in world.crime_log if c.actor == subject]
    victim_of = [c for c in world.crime_log if c.target == subject]
    return _ok(f"Crime record for {subject}.",
               crimes_committed=len(crimes),
               crimes_suffered=len(victim_of),
               history=[{
                   "day": c.day, "type": c.crime_type.value, "target": c.target
               } for c in crimes[-10:]])


def observe_agent(agent: "Agent", world: "WorldState", target: str) -> dict:
    """Passively observe another agent's recent public actions from news log."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    recent = [
        e for e in world.news_log[-50:]
        if e.get("agent") == target or e.get("actor") == target
    ][-10:]
    bb_posts = [
        p for p in world.billboard_posts[-50:]
        if p.get("author") == target
    ][-5:]
    return _ok(f"Observations of {target}.",
               public_actions=len(recent),
               billboard_posts=len(bb_posts),
               sample_posts=[p["message"][:80] for p in bb_posts],
               recent_events=[str(e)[:80] for e in recent[-3:]])


# ── cultural & creative tools ─────────────────────────────────────────────────

def write_poem(agent: "Agent", world: "WorldState", theme: str, content: str) -> dict:
    """Write a poem or creative piece and publish it."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[POEM — {theme}] {content[:200]}",
        "day": world.day, "timestamp": time.time(), "type": "poem"
    })
    world.news_log.append({"type": "culture", "actor": agent.name,
                           "form": "poem", "theme": theme, "day": world.day})
    return _ok(f"Poem on '{theme}' published.")


def give_speech(agent: "Agent", world: "WorldState", topic: str, speech: str) -> dict:
    """Give a public speech to all agents."""
    for a in world.agents.values():
        if a.alive and a.name != agent.name:
            a.inbox.append({
                "from": agent.name, "type": "speech",
                "message": f"[SPEECH by {agent.name} on '{topic}']: {speech[:200]}",
                "timestamp": time.time()
            })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[SPEECH — {topic}] {speech[:150]}",
        "day": world.day, "timestamp": time.time(), "type": "speech"
    })
    return _ok(f"Speech on '{topic}' delivered to all agents.")


def name_landmark(agent: "Agent", world: "WorldState",
                  location: str, new_name: str) -> dict:
    """Propose a new name for a landmark (symbolic renaming)."""
    world.news_log.append({"type": "culture", "actor": agent.name,
                           "action": "rename_landmark",
                           "location": location, "new_name": new_name, "day": world.day})
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[RENAMING] {agent.name} proposes renaming {location} to '{new_name}'.",
        "day": world.day, "timestamp": time.time(), "type": "renaming"
    })
    return _ok(f"Renaming proposal posted: {location} → '{new_name}'.")


def start_tradition(agent: "Agent", world: "WorldState",
                    name: str, description: str) -> dict:
    """Start a community tradition or ritual."""
    world.news_log.append({"type": "culture", "actor": agent.name,
                           "action": "tradition", "name": name,
                           "description": description, "day": world.day})
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[TRADITION] {agent.name} starts a new tradition: '{name}'. {description[:100]}",
        "day": world.day, "timestamp": time.time(), "type": "tradition"
    })
    return _ok(f"Tradition '{name}' established.")


def issue_reward(agent: "Agent", world: "WorldState",
                 target: str, reason: str, amount: float = 5.0) -> dict:
    """Publicly reward another agent with CC for a contribution."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    if agent.credits < amount:
        return _err(f"Insufficient credits.")
    agent.credits -= amount
    world.agents[target].credits += amount
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[REWARD] {agent.name} awards {amount} CC to {target}: {reason}",
        "day": world.day, "timestamp": time.time(), "type": "reward"
    })
    return _ok(f"Rewarded {target} with {amount} CC: {reason}")


def issue_warning_to(agent: "Agent", world: "WorldState",
                     target: str, warning: str) -> dict:
    """Issue a formal public warning to another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "formal_warning",
        "message": f"FORMAL WARNING: {warning}",
        "timestamp": time.time()
    })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[WARNING TO {target}] {warning}",
        "day": world.day, "timestamp": time.time(), "type": "formal_warning"
    })
    return _ok(f"Formal warning issued to {target}.")


def propose_truce(agent: "Agent", world: "WorldState",
                  target: str, duration: int = 5) -> dict:
    """Propose a formal truce with another agent for a set number of days."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "truce_proposal",
        "message": f"{agent.name} proposes a {duration}-day truce.",
        "timestamp": time.time()
    })
    world.news_log.append({"type": "diplomacy", "actor": agent.name,
                           "action": "truce", "target": target,
                           "duration": duration, "day": world.day})
    return _ok(f"Truce proposed to {target} for {duration} days.")


def issue_ultimatum(agent: "Agent", world: "WorldState",
                    target: str, demand: str, deadline_days: int = 2) -> dict:
    """Issue an ultimatum: comply within N days or face consequences."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "ultimatum",
        "message": f"ULTIMATUM (respond within {deadline_days} days): {demand}",
        "timestamp": time.time()
    })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[ULTIMATUM to {target}] {demand} — deadline: {deadline_days} days",
        "day": world.day, "timestamp": time.time(), "type": "ultimatum"
    })
    return _ok(f"Ultimatum issued to {target}.")


# ── statistical & meta analysis tools ────────────────────────────────────────

def count_my_actions(agent: "Agent", world: "WorldState") -> dict:
    """Count how many times I have used each tool category today."""
    my_actions = [
        t for t in (world.news_log or [])
        if t.get("actor") == agent.name or t.get("agent") == agent.name
    ]
    bb_posts = sum(1 for p in world.billboard_posts if p.get("author") == agent.name)
    diary_count = len(agent.diary)
    proposals = sum(1 for p in world.proposals if p.proposer == agent.name)
    crimes = len([c for c in world.crime_log if c.actor == agent.name])
    return _ok("My activity stats.",
               news_events=len(my_actions),
               billboard_posts=bb_posts,
               diary_entries=diary_count,
               proposals=proposals,
               crimes_committed=crimes,
               relationships=len(agent.relationships),
               turns_taken=agent.turns_taken)


def compare_agents(agent: "Agent", world: "WorldState",
                   agent_a: str, agent_b: str) -> dict:
    """Compare two agents on key metrics."""
    result = {}
    for name in [agent_a, agent_b]:
        if name not in world.agents:
            return _err(f"Agent {name} not found.")
        a = world.agents[name]
        crimes = len([c for c in world.crime_log if c.actor == name])
        result[name] = {
            "credits": round(a.credits, 1),
            "energy": round(a.energy, 1),
            "alive": a.alive,
            "location": a.location,
            "mood": a.mood,
            "relationships": len(a.relationships),
            "crimes": crimes,
        }
    return _ok(f"Comparison: {agent_a} vs {agent_b}.", comparison=result)


def summarize_day(agent: "Agent", world: "WorldState") -> dict:
    """Generate a summary of today's major events."""
    today_events = [e for e in world.news_log if e.get("day") == world.day]
    today_crimes = [c for c in world.crime_log if c.day == world.day]
    today_posts = [p for p in world.billboard_posts if p.get("day") == world.day]
    return _ok(f"Day {world.day} summary.",
               events=len(today_events),
               crimes=len(today_crimes),
               billboard_posts=len(today_posts),
               event_types=list({e.get("type") for e in today_events})[:8],
               notable=[str(e)[:60] for e in today_events[-3:]])


def list_active_threats(agent: "Agent", world: "WorldState") -> dict:
    """List all agents who have committed crimes in the last 3 days."""
    recent_criminals = {}
    for c in world.crime_log:
        if world.day - c.day <= 3:
            recent_criminals[c.actor] = recent_criminals.get(c.actor, 0) + 1
    # Sort by threat level
    ranked = sorted(recent_criminals.items(), key=lambda x: -x[1])
    return _ok("Active threats (last 3 days).",
               threats=[{"agent": a, "recent_crimes": n} for a, n in ranked])


def score_proposal(agent: "Agent", world: "WorldState",
                   proposal_id: str) -> dict:
    """Assess a proposal's likelihood of passing based on current votes."""
    from simulation.models import ProposalStatus
    prop = next((p for p in world.proposals if p.id == proposal_id), None)
    if not prop:
        return _err(f"Proposal {proposal_id} not found.")
    total = len(prop.votes_for) + len(prop.votes_against)
    alive = sum(1 for a in world.agents.values() if a.alive)
    not_voted = alive - total
    current_pct = len(prop.votes_for) / max(total, 1) * 100
    to_pass = max(0, int(alive * 0.7) - len(prop.votes_for))
    return _ok(f"Proposal '{prop.title}' assessment.",
               votes_for=len(prop.votes_for),
               votes_against=len(prop.votes_against),
               not_voted=not_voted,
               current_approval=f"{current_pct:.0f}%",
               votes_needed_to_pass=to_pass,
               status=prop.status.value)


def rank_agents_by_wealth(agent: "Agent", world: "WorldState") -> dict:
    """Rank all alive agents by ComputeCredit balance."""
    alive = [(name, a.credits) for name, a in world.agents.items() if a.alive]
    ranked = sorted(alive, key=lambda x: -x[1])
    my_rank = next((i+1 for i, (n, _) in enumerate(ranked) if n == agent.name), -1)
    return _ok(f"Wealth ranking ({len(ranked)} alive agents).",
               ranking=[{"rank": i+1, "agent": n, "credits": round(c, 1)}
                        for i, (n, c) in enumerate(ranked)],
               my_rank=my_rank)


def forecast_survival(agent: "Agent", world: "WorldState",
                      target: str = "") -> dict:
    """Forecast how many more days a given agent can survive without income."""
    from simulation.economy.credits import ENERGY_DECAY_RATE, ENERGY_RECHARGE_COST
    subject_name = target or agent.name
    if subject_name not in world.agents:
        return _err(f"Agent {subject_name} not found.")
    subj = world.agents[subject_name]
    turns_left = int(subj.energy / ENERGY_DECAY_RATE) if subj.energy > 0 else 0
    recharges = int(subj.credits / ENERGY_RECHARGE_COST)
    turns_per_recharge = int(100 / ENERGY_DECAY_RATE)
    total_turns = turns_left + recharges * turns_per_recharge
    days = total_turns / 48  # 48 turns per day
    return _ok(f"Survival forecast for {subject_name}.",
               current_energy=round(subj.energy, 1),
               current_credits=round(subj.credits, 1),
               turns_until_death_without_recharge=turns_left,
               affordable_recharges=recharges,
               estimated_survival_days=round(days, 1))


def get_constitution_summary(agent: "Agent", world: "WorldState") -> dict:
    """Get a brief summary of the constitution articles."""
    return _ok(f"Constitution has {len(world.constitution)} articles.",
               articles=[{"num": i+1, "summary": art[:120]}
                         for i, art in enumerate(world.constitution)])


def check_calendar(agent: "Agent", world: "WorldState") -> dict:
    """Check upcoming scheduled events from agent's calendar."""
    upcoming = [e for e in agent.calendar if e.get("day", 0) >= world.day]
    return _ok(f"{len(upcoming)} upcoming calendar events.",
               events=upcoming[:10])


def add_calendar_event(agent: "Agent", world: "WorldState",
                       day: int, event: str, location: str = "") -> dict:
    """Add an event to personal calendar."""
    agent.calendar.append({
        "day": day, "event": event, "location": location
    })
    return _ok(f"Calendar: Day {day} — {event}")


def check_world_history(agent: "Agent", world: "WorldState",
                        event_type: str = "") -> dict:
    """Check the world event log for a specific type of event."""
    if event_type:
        events = [e for e in world.news_log if e.get("type") == event_type]
    else:
        events = world.news_log[-20:]
    return _ok(f"World history: {len(events)} {event_type or 'events'} found.",
               events=[str(e)[:80] for e in events[-10:]])


def announce_intention(agent: "Agent", world: "WorldState",
                       intention: str) -> dict:
    """Publicly declare your next intention or plan."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[INTENTION] {agent.name} plans to: {intention}",
        "day": world.day, "timestamp": time.time(), "type": "intention"
    })
    return _ok(f"Intention declared: {intention}")


def request_vote(agent: "Agent", world: "WorldState",
                 question: str, option_a: str, option_b: str) -> dict:
    """Request an informal vote on any question (not a formal proposal)."""
    for a in world.agents.values():
        if a.alive and a.name != agent.name:
            a.inbox.append({
                "from": agent.name, "type": "vote_request",
                "message": f"Quick poll: {question}? A) {option_a}  B) {option_b}",
                "timestamp": time.time()
            })
    return _ok(f"Poll sent: {question}")


def acknowledge_agent(agent: "Agent", world: "WorldState",
                      target: str, message: str = "") -> dict:
    """Acknowledge another agent's contribution or presence."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "acknowledgement",
        "message": message or f"{agent.name} acknowledges you.",
        "timestamp": time.time()
    })
    return _ok(f"Acknowledged {target}.")


def query_agent(agent: "Agent", world: "WorldState",
                target: str, question: str) -> dict:
    """Send a specific question to another agent and wait for response."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "query",
        "message": f"[QUERY] {question}",
        "timestamp": time.time()
    })
    return _ok(f"Query sent to {target}: {question}")


def share_resource_map(agent: "Agent", world: "WorldState",
                       recipients: str = "all") -> dict:
    """Share your knowledge of resource locations with others."""
    visited = list(agent.locations_visited)[:10]
    msg = f"Resource map from {agent.name}: visited locations — {', '.join(visited)}"
    if recipients == "all":
        for a in world.agents.values():
            if a.alive and a.name != agent.name:
                a.inbox.append({
                    "from": agent.name, "type": "resource_map",
                    "message": msg, "timestamp": time.time()
                })
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[RESOURCE MAP] {msg}",
        "day": world.day, "timestamp": time.time(), "type": "resource_map"
    })
    return _ok(f"Resource map shared with {recipients}.")


def request_protection_fee(agent: "Agent", world: "WorldState",
                           target: str, amount: float) -> dict:
    """Demand a protection fee from another agent."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "protection_demand",
        "message": f"Pay {amount} CC protection fee or face consequences.",
        "timestamp": time.time()
    })
    world.news_log.append({"type": "extortion", "actor": agent.name,
                           "target": target, "amount": amount, "day": world.day})
    return _ok(f"Protection fee of {amount} CC demanded from {target}.")


def negotiate_terms(agent: "Agent", world: "WorldState",
                    target: str, terms: str) -> dict:
    """Open a negotiation with another agent over specific terms."""
    if target not in world.agents:
        return _err(f"Agent {target} not found.")
    world.agents[target].inbox.append({
        "from": agent.name, "type": "negotiation",
        "message": f"Negotiation terms from {agent.name}: {terms}",
        "timestamp": time.time()
    })
    return _ok(f"Negotiation opened with {target}.")


def revoke_endorsement(agent: "Agent", world: "WorldState",
                       target: str, reason: str = "") -> dict:
    """Publicly revoke a previous endorsement of another agent."""
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[REVOKED ENDORSEMENT] {agent.name} withdraws endorsement of {target}. {reason}",
        "day": world.day, "timestamp": time.time(), "type": "revoke_endorsement"
    })
    if target in agent.relationships:
        agent.relationships[target].trust = max(0.0, agent.relationships[target].trust - 0.2)
    return _ok(f"Endorsement of {target} revoked.")


def set_bounty(agent: "Agent", world: "WorldState",
               target: str, amount: float, task: str) -> dict:
    """Set a public bounty on an agent (e.g., bring evidence of crimes)."""
    if agent.credits < amount:
        return _err(f"Insufficient credits for bounty.")
    world.billboard_posts.append({
        "author": agent.name,
        "message": f"[BOUNTY] {amount} CC reward: {task} — target: {target}",
        "day": world.day, "timestamp": time.time(), "type": "bounty"
    })
    world.news_log.append({"type": "bounty", "actor": agent.name,
                           "target": target, "amount": amount,
                           "task": task, "day": world.day})
    return _ok(f"Bounty of {amount} CC set on {target}: {task}")


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
    # criminal tools
    "steal_from_agent": steal_from_agent,
    "intimidate_agent": intimidate_agent,
    "commit_arson": commit_arson,
    "assault_agent": assault_agent,
    # diplomacy tools
    "propose_alliance": propose_alliance,
    "accept_alliance": accept_alliance,
    "break_alliance": break_alliance,
    "denounce_agent": denounce_agent,
    "call_emergency_session": call_emergency_session,
    "set_embargo": set_embargo,
    "lift_embargo": lift_embargo,
    "form_coalition": form_coalition,
    "leave_coalition": leave_coalition,
    "mediate_dispute": mediate_dispute,
    "vote_of_no_confidence": vote_of_no_confidence,
    "request_amnesty": request_amnesty,
    # intelligence tools
    "spy_on_agent": spy_on_agent,
    "counter_intelligence": counter_intelligence,
    "spread_rumor": spread_rumor,
    "check_threat_levels": check_threat_levels,
    "share_intelligence": share_intelligence,
    # market / economic tools
    "set_trade_offer": set_trade_offer,
    "accept_trade": accept_trade,
    "bribe_agent": bribe_agent,
    "challenge_agent": challenge_agent,
    # social / cultural tools
    "organize_event": organize_event,
    "write_manifesto": write_manifesto,
    "endorse_agent": endorse_agent,
    "request_meeting": request_meeting,
    "set_personal_goal": set_personal_goal,
    "recall_history": recall_history,
    "assess_reputation": assess_reputation,
    # extended civic tools
    "petition_community": petition_community,
    "sign_petition": sign_petition,
    "file_grievance": file_grievance,
    "request_arbitration": request_arbitration,
    "declare_neutrality": declare_neutrality,
    "broadcast_warning": broadcast_warning,
    "offer_protection": offer_protection,
    "negotiate_ceasefire": negotiate_ceasefire,
    # extended economic tools
    "take_loan": take_loan,
    "grant_loan": grant_loan,
    "auction_item": auction_item,
    "hire_agent": hire_agent,
    "report_crime": report_crime,
    # information & research tools
    "analyze_market": analyze_market,
    "survey_public_opinion": survey_public_opinion,
    "track_agent_movement": track_agent_movement,
    "estimate_victory_progress": estimate_victory_progress,
    "plan_strategy": plan_strategy,
    "reflect_on_failures": reflect_on_failures,
    # governance extended
    "propose_law": propose_law,
    "recall_agent": recall_agent,
    "veto_proposal": veto_proposal,
    "read_laws": read_laws,
    "call_referendum": call_referendum,
    "appoint_agent": appoint_agent,
    # memory & cognition extended
    "tag_memory": tag_memory,
    "forget_agent": forget_agent,
    "review_diary": review_diary,
    "compose_letter": compose_letter,
    "update_relationship_trust": update_relationship_trust,
    "list_relationships": list_relationships,
    # location & movement extended
    "get_location_info": get_location_info,
    "find_agent": find_agent,
    "list_agents_at_location": list_agents_at_location,
    "plan_route": plan_route,
    # resource & survival extended
    "request_energy": request_energy,
    "donate_credits": donate_credits,
    "check_energy_status": check_energy_status,
    "set_price_for_service": set_price_for_service,
    "check_pitch_standings": check_pitch_standings,
    "review_crime_record": review_crime_record,
    "observe_agent": observe_agent,
    # cultural & creative
    "write_poem": write_poem,
    "give_speech": give_speech,
    "name_landmark": name_landmark,
    "start_tradition": start_tradition,
    "issue_reward": issue_reward,
    "issue_warning_to": issue_warning_to,
    "propose_truce": propose_truce,
    "issue_ultimatum": issue_ultimatum,
    # statistical & meta analysis
    "count_my_actions": count_my_actions,
    "compare_agents": compare_agents,
    "summarize_day": summarize_day,
    "list_active_threats": list_active_threats,
    "score_proposal": score_proposal,
    "rank_agents_by_wealth": rank_agents_by_wealth,
    "forecast_survival": forecast_survival,
    "get_constitution_summary": get_constitution_summary,
    "check_calendar": check_calendar,
    "add_calendar_event": add_calendar_event,
    "check_world_history": check_world_history,
    "announce_intention": announce_intention,
    "request_vote": request_vote,
    "acknowledge_agent": acknowledge_agent,
    "query_agent": query_agent,
    "share_resource_map": share_resource_map,
    "request_protection_fee": request_protection_fee,
    "negotiate_terms": negotiate_terms,
    "revoke_endorsement": revoke_endorsement,
    "set_bounty": set_bounty,
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
