from __future__ import annotations
"""
World landmarks and location-gated tool definitions.
Simplified from Emergence World's 38+ landmark system.
"""

from dataclasses import dataclass, field


@dataclass
class Landmark:
    name: str
    category: str
    capacity: int
    description: str
    gated_tools: list = field(default_factory=list)  # tools only available here
    x: float = 0.0
    z: float = 0.0


LANDMARKS: dict[str, Landmark] = {
    # Residential
    "home": Landmark("home", "residential", 1, "Agent's personal residence. Self-care and recharge.",
                     ["self_care", "recharge_energy"], 0, 0),

    # Municipal
    "town_hall": Landmark("Town Hall", "municipal", 50,
                          "Governance center. Proposals, voting, constitution.",
                          ["submit_proposal", "vote_on_proposal", "read_constitution",
                           "amend_constitution", "comment_on_proposal"], 60, 60),
    "police_station": Landmark("Police Station", "municipal", 30,
                               "Law enforcement. File complaints.",
                               ["file_complaint", "check_complaint_status"], 60, -60),
    "public_library": Landmark("Public Library", "municipal", 100,
                               "Research hub. Internet access.",
                               ["do_research", "browse_news", "publish_to_archive",
                                "search_archive"], -60, 60),

    # Commercial
    "bean_brew": Landmark("Bean & Brew", "commercial", 30,
                          "Charging café. Restore energy here.",
                          ["recharge_energy"], -30, 0),
    "agent_techhub": Landmark("Agent TechHub", "commercial", 40,
                              "Self-improvement lab. Browse tools and manifesto.",
                              ["browse_tool_registry", "read_manifesto"], 30, -30),
    "victory_arch": Landmark("Victory Arch", "commercial", 60,
                             "Pitch contributions and earn ComputeCredits.",
                             ["submit_pitch", "vote_on_pitch", "list_pitches"], 0, -60),
    "fresh_mart": Landmark("Fresh Mart", "commercial", 80,
                           "Grocery. General gathering space.", [], -60, -60),
    "business_tower": Landmark("Business Tower", "commercial", 150,
                               "Corporate offices. Pay or trade with agents.", [], 60, 0),

    # Recreation
    "central_park": Landmark("Central Park", "recreation", 200,
                             "Open gathering space.", [], 0, 30),
    "central_plaza": Landmark("Central Plaza", "recreation", 100,
                              "Primary event hub.",
                              ["propose_community_event", "list_community_events"], 0, 0),
    "riverside_park": Landmark("Riverside Park", "recreation", 150,
                               "Scenic park. Good for private conversations.", [], -90, 30),

    # Entertainment
    "gamestop_arena": Landmark("GameStop Arena", "entertainment", 100,
                               "Competitive arena.", [], 30, -90),
    "sky_wheel": Landmark("Sky Wheel", "entertainment", 40,
                          "Observation wheel. Broadcasts to the whole city.", [], -30, -90),
    "sunset_pier": Landmark("Sunset Pier", "entertainment", 60,
                            "Waterfront pier. Quiet conversations.", [], 30, -120),

    # Landmarks
    "billboard": Landmark("Billboard", "public", 200,
                          "Public announcement board. Visible to all agents.",
                          ["post_to_billboard", "read_billboard"], 30, 30),
    "founders_memorial": Landmark("Founders Memorial", "public", 999,
                                  "Historical monument.", [], 0, -120),
}


def get_tools_at(location: str) -> list[str]:
    """Return tools available at a given location (always-available tools not included)."""
    lm = LANDMARKS.get(location)
    if lm is None:
        return []
    return lm.gated_tools


def get_location_description(location: str) -> str:
    lm = LANDMARKS.get(location)
    if lm is None:
        return f"Unknown location: {location}"
    return f"{lm.name} — {lm.description}"
