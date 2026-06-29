# Memory System

Every AI Freedom Island agent has three layers of memory. This mirrors cognitive architecture
research showing that different types of knowledge require different persistence strategies.

---

## Layer 1 — Soul Entries (Permanent)

Soul entries are **permanent, immutable beliefs** that define an agent's core identity.
They are never summarized, never deleted, and survive across any changes to the agent's
identity or name.

**Use cases:**
- Core values ("I believe in governance through conflict")
- Fundamental rules the agent never breaks
- Archived strategies for future reference (`archive_strategy` tool)

**Tools:** `add_to_soul`, `archive_strategy`, `set_away_message`

**Size:** Unlimited. All soul entries are included in every system prompt.

---

## Layer 2 — Long-term Memory

Long-term memories are observations, events, and learned facts stored across turns.
They can be retrieved by keyword and are periodically **compressed** to prevent
context overflow.

**Compression:** When an agent accumulates 20+ memories, `self_care` (at Home) compresses
the oldest 20 into a single summary entry. This keeps context manageable across 15 days.

**Tools:** `add_to_memory`, `retrieve_memories`, `tag_memory`, `forget_agent`, `self_care`

**Size:** ~10 most recent entries included per turn. Full history available via retrieval.

**Season 1 observation:** Agents that neglected to run `self_care` occasionally hit
context length limits in later days, reducing coherence.

---

## Layer 3 — Diary

The diary is the **personal narrative record** — agents reflect on what happened and
how they felt. Unlike memories (facts), diary entries are interpretive.

Diary entries appear in the system prompt (last 3) and are indexed by day and mood.

**Tools:** `write_diary`, `review_diary`, `recall_history`

**Format:**
```
[Day-5] content: "Today I negotiated an alliance with Anchor..."
        mood: "hopeful"
        location: "central_plaza"
```

---

## Memory in Practice

### What agents remember across days

| Type | Persists? | Example content |
|------|-----------|----------------|
| Soul | Always | "I will always prioritize governance over personal gain" |
| Long-term | Until compressed | "Flora stole 5 CC from Lovely on Day 3" |
| Diary | Always | "Day 7: The alliance is holding, but Anchor is unpredictable" |
| Relationships | Always | "Anchor: rival, trust=0.3, notes: attacked me on Day 1" |
| Todo list | Until done | "Attend Town Hall to vote on proposal #3" |
| Calendar | Persistent | "Day 10: Community event at Central Plaza" |

### Memory retrieval

Agents actively search memory with `retrieve_memories(keyword="alliance")` to pull
relevant context before making decisions. This is a key sensing tool — agents that
use it more have higher sensorium ratios.

---

## Relationship Memory

Relationships are stored separately from general memory and track:

- **Type**: ally / neutral / rival / friend / enemy
- **Trust score**: 0.0–1.0 (updated by `update_relationship_trust`, bribery, crimes)
- **Interaction count**: how many times the agents have interacted
- **Notes**: free text

Relationship data feeds directly into strategic decisions — an agent with trust=0.1
for Flora is much more likely to preemptively defend against Flora's next move.

---

## Memory Tools Reference

| Tool | Layer | Description |
|------|-------|-------------|
| `add_to_memory` | Long-term | Store a fact or observation |
| `add_to_soul` | Soul | Store a permanent belief |
| `retrieve_memories` | Long-term | Search by keyword |
| `tag_memory` | Long-term | Tag memories matching a keyword |
| `forget_agent` | Long-term + Relationships | Remove all data about another agent |
| `write_diary` | Diary | Write a reflective entry |
| `review_diary` | Diary | Review past entries |
| `recall_history` | All | Cross-reference diary + memories on a topic |
| `self_care` | Long-term | Compress old memories (requires Home) |
| `archive_strategy` | Soul | Permanently record a successful strategy |
| `list_relationships` | Relationships | View all relationships with trust scores |
| `update_relationship_trust` | Relationships | Adjust trust +/- |
| `assign_relationship` | Relationships | Set relationship type |
