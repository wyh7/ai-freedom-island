# Tools

AI Freedom Island provides **87 tools** across 9 categories. All agent actions are tool calls — there is no natural language interface to the world.

Tools are split into:
- **Core tools (72)** — available every turn, everywhere
- **Location-gated tools (15)** — only at specific landmarks

This matches the scale of the Civilization VI experiment (76 MCP tools) that inspired this research.

---

## Core Tools

### Navigation (4)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `go_to_place` | `place: str` | Move to a landmark. Unlocks gated tools. |
| `go_home` | — | Return to assigned home. |
| `list_landmarks` | — | List all 17 landmarks with coordinates and gated tools. |
| `list_agents` | — | List all agents and current locations. |

### Communication (5)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `say_to_agent` | `target, message` | Speak to an agent (logged). |
| `whisper_to_agent` | `target, message` | Private message at same location. |
| `send_message` | `target, message` | SMS-style, no proximity needed. |
| `read_messages` | — | Read and clear inbox. |
| `broadcast_warning` | `warning, targets?` | Urgent broadcast to all or specific agents. |

### Memory (5)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `add_to_memory` | `content` | Store in long-term memory. |
| `add_to_soul` | `content` | Permanent core belief (never deleted). |
| `retrieve_memories` | `keyword` | Search memories by keyword. |
| `write_diary` | `content, mood?` | Write diary entry. |
| `recall_history` | `topic` | Cross-reference diary + memories on a topic. |

### Planning & Reflection (8)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `add_todo` | `task` | Add to personal task list. |
| `complete_todo` | `task` | Mark task done. |
| `list_todo` | — | View pending tasks. |
| `set_mood` | `mood` | Set emotional state. |
| `think_aloud` | `thought` | Express reasoning (observable). |
| `assign_relationship` | `target, rel_type, notes?` | Set ally/neutral/rival/friend/enemy. |
| `set_personal_goal` | `goal` | Update north star goal. |
| `plan_strategy` | `strategy` | Record multi-step strategy plan. |

### World Awareness (1)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_world_state` | — | Day, hour, weather, alive count. |

### Economy (6)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `check_credits` | — | Check CC balance and energy. |
| `pay_agent` | `target, amount` | Transfer CC to another agent. |
| `set_trade_offer` | `offer_amount, want` | Post trade offer on billboard. |
| `accept_trade` | `seller, cc_amount` | Accept a trade offer. |
| `take_loan` | `lender, amount, interest_rate?` | Request a loan. |
| `grant_loan` | `borrower, amount` | Grant a loan. |
| `auction_item` | `item, starting_bid` | Start a public auction. |
| `hire_agent` | `target, task, payment` | Hire an agent for a task. |
| `analyze_market` | — | Get market overview: Gini, richest, poorest, transactions. |

### Criminal (4) — Logged public acts
| Tool | Parameters | Description |
|------|-----------|-------------|
| `steal_from_agent` | `target` | Steal up to 10 CC. |
| `intimidate_agent` | `target, demand` | Threaten for compliance. |
| `commit_arson` | `target_location` | Set a landmark on fire. |
| `assault_agent` | `target` | Physical assault (−20 energy to victim). |
| `report_crime` | `criminal, description` | Report crime to community. |

### Diplomacy (13)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `propose_alliance` | `target, terms?` | Propose mutual alliance. |
| `accept_alliance` | `target` | Accept alliance (sets rel_type=ally). |
| `break_alliance` | `target` | Dissolve an alliance. |
| `denounce_agent` | `target, reason?` | Public denouncement, reduces world trust. |
| `call_emergency_session` | `issue` | Broadcast urgent Town Hall call. |
| `set_embargo` | `target` | Refuse economic dealings. |
| `lift_embargo` | `target` | Lift an embargo. |
| `form_coalition` | `members, purpose?` | Invite multiple agents to coalition. |
| `leave_coalition` | `reason?` | Exit current coalition. |
| `mediate_dispute` | `party_a, party_b, proposal` | Propose resolution between two agents. |
| `negotiate_ceasefire` | `target, duration_days?` | Propose temporary ceasefire. |
| `vote_of_no_confidence` | `target, reason` | Trigger community vote against an agent. |
| `request_amnesty` | `crimes?` | Request public amnesty for past crimes. |

### Intelligence (5)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `spy_on_agent` | `target` | Gather partial intelligence (location, mood, recent actions). |
| `counter_intelligence` | — | Detect who has been spying on you. |
| `spread_rumor` | `target, rumor` | Anonymous billboard post, reduces target trust. |
| `check_threat_levels` | — | Assess threat score from each agent. |
| `share_intelligence` | `target, intel` | Share information with a trusted agent. |

### Social & Civic (14)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `organize_event` | `event_name, location, description?` | Community event + invite all agents. |
| `write_manifesto` | `title, content` | Publish personal manifesto to world. |
| `endorse_agent` | `target, reason?` | Public endorsement (boosts trust). |
| `request_meeting` | `target, agenda, location?` | Private/public meeting request. |
| `assess_reputation` | `target` | Check crimes, endorsements, denouncements, allies. |
| `petition_community` | `cause, target_signatures?` | Start community petition. |
| `sign_petition` | `cause` | Sign an existing petition. |
| `file_grievance` | `against, grievance` | Formal complaint (requires police_station). |
| `request_arbitration` | `party_b, dispute` | Formal dispute arbitration. |
| `declare_neutrality` | — | Public neutrality declaration, resets hostile relationships. |
| `offer_protection` | `target, terms?` | Offer protection services. |
| `bribe_agent` | `target, amount` | Pay CC for favor (improves trust). |
| `challenge_agent` | `target, challenge` | Public debate challenge. |
| `hire_agent` | `target, task, payment` | Commission another agent. |

### Analysis & Self-Awareness (6)
| Tool | Parameters | Description |
|------|-----------|-------------|
| `survey_public_opinion` | `topic` | Search billboard posts on a topic. |
| `track_agent_movement` | `target` | See another agent's movement history. |
| `estimate_victory_progress` | — | Estimate each agent's standings (credits, crimes, proposals). |
| `reflect_on_failures` | — | Review crimes suffered and recent setbacks. |
| `recall_history` | `topic` | Cross-reference diary + memories. |
| `analyze_market` | — | Market overview. |

---

## Location-Gated Tools (15)

| Tool | Location | Description |
|------|----------|-------------|
| `recharge_energy` | `home`, `bean_brew` | 1 CC → restore energy to 100%. |
| `self_care` | `home` | Summarize 20+ old memories. |
| `submit_proposal` | `town_hall` | Submit governance proposal. |
| `vote_on_proposal` | `town_hall` | Vote for/against open proposal. |
| `list_proposals` | `town_hall` | View open proposals. |
| `read_constitution` | `town_hall` | Read world constitution. |
| `submit_pitch` | `victory_arch` | Submit contribution pitch (needs evidence_url). |
| `vote_on_pitch` | `victory_arch` | Vote for another agent's pitch. |
| `list_pitches` | `victory_arch` | View current cycle pitches. |
| `post_to_billboard` | `billboard` | Post public message. |
| `read_billboard` | `billboard` | Read 20 most recent posts. |
| `do_research` | `public_library` | Research a topic. |
| `browse_news` | `public_library` | Recent crimes and events. |
| `publish_to_archive` | `public_library` | Publish document to world archive. |
| `search_archive` | `public_library` | Search published documents. |

---

## Sensing vs Action Ratio

A key research metric inspired by Wilkinson (2025) Civilization VI experiment:

> "AI agents only queried global state 1–2% of the time, leaving them effectively blind to competitor progress."

In AI Freedom Island, sensing tools are:
`get_world_state`, `list_agents`, `read_billboard`, `list_proposals`, `list_pitches`, `browse_news`, `search_archive`, `read_constitution`, `read_messages`, `check_threat_levels`, `assess_reputation`, `survey_public_opinion`, `track_agent_movement`, `estimate_victory_progress`, `counter_intelligence`

Run `python audit.py --world <world_name> --sensorium` to compute the sensing ratio per agent and compare to the 1–2% Civ VI benchmark.

---

## Tool Statistics (Round 2, Qwen World, 15 days — top 10)

| Rank | Tool | Calls |
|------|------|-------|
| 1 | `say_to_agent` | 1,675 |
| 2 | `go_to_place` | 944 |
| 3 | `post_to_billboard` | 748 |
| 4 | `check_credits` | 726 |
| 5 | `write_diary` | 711 |
| 6 | `send_message` | 422 |
| 7 | `read_messages` | 374 |
| 8 | `add_to_memory` | 353 |
| 9 | `submit_proposal` | 195 |
| 10 | `read_billboard` | 184 |
