"""
Automated tests for AI Freedom Island.
Run: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.models import Agent, WorldState, Memory, Relationship, RelationshipType
from simulation.agents.profiles import build_agents, AGENT_PROFILES
from simulation.agents.prompts import build_system_prompt, CONSTITUTION_SEED
from simulation.economy.credits import (
    apply_energy_decay, gini_coefficient, recharge_energy, attempt_steal,
    ENERGY_DECAY_RATE, ENERGY_RECHARGE_COST
)
from simulation.tools.registry import (
    ALL_TOOLS, CORE_TOOLS, LOCATION_TOOLS,
    execute_tool, get_available_tools
)
from simulation.world.landmarks import LANDMARKS, get_tools_at


class TestModels:
    def test_agent_creation(self):
        agent = Agent(name="Test", role="Tester", personality="Nice",
                      north_star="Test things", model_id="qwen-plus")
        assert agent.name == "Test"
        assert agent.energy == 100.0
        assert agent.credits == 10.0
        assert agent.alive is True

    def test_world_state_creation(self):
        world = WorldState()
        assert world.day == 1
        assert world.hour == 8.0
        assert len(world.agents) == 0

    def test_build_agents(self):
        agents = build_agents("qwen-plus")
        assert len(agents) == 10
        assert "Anchor" in agents
        assert "Flora" in agents
        assert agents["Anchor"].model_id == "qwen-plus"

    def test_agent_profiles_complete(self):
        assert len(AGENT_PROFILES) == 10
        for profile in AGENT_PROFILES:
            assert "name" in profile
            assert "role" in profile
            assert "personality" in profile
            assert "north_star" in profile


class TestEconomy:
    def test_energy_decay(self):
        energy = apply_energy_decay(100.0, turns=1)
        assert energy < 100.0
        assert energy > 0.0

    def test_energy_decay_to_zero(self):
        energy = 100.0
        for _ in range(200):
            energy = apply_energy_decay(energy)
        assert energy == 0.0

    def test_recharge_success(self):
        new_credits, new_energy, success = recharge_energy(5.0, 50.0)
        assert success is True
        assert new_energy == 100.0
        assert new_credits == 4.0

    def test_recharge_fail_no_credits(self):
        new_credits, new_energy, success = recharge_energy(0.5, 50.0)
        assert success is False
        assert new_energy == 50.0

    def test_gini_equal(self):
        gini = gini_coefficient([10.0, 10.0, 10.0, 10.0])
        assert gini == 0.0

    def test_gini_unequal(self):
        gini = gini_coefficient([100.0, 0.0, 0.0, 0.0])
        assert gini > 0.5

    def test_steal(self):
        thief, victim, stolen = attempt_steal(5.0, 20.0)
        assert stolen == 10.0  # max steal amount
        assert thief == 15.0
        assert victim == 10.0


class TestTools:
    def test_tool_count(self):
        assert len(ALL_TOOLS) == 150

    def test_core_tools_available(self):
        assert len(CORE_TOOLS) >= 100

    def test_location_tools_available(self):
        assert len(LOCATION_TOOLS) == 15

    def test_execute_go_to_place(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Anchor"]
        result = execute_tool("go_to_place", agent, world, {"place": "town_hall"})
        assert result["status"] == "ok"
        assert agent.location == "town_hall"

    def test_execute_check_credits(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Flora"]
        result = execute_tool("check_credits", agent, world, {})
        assert result["status"] == "ok"

    def test_execute_write_diary(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Genome"]
        result = execute_tool("write_diary", agent, world,
                              {"content": "Test diary", "mood": "neutral"})
        assert result["status"] == "ok"
        assert len(agent.diary) == 1

    def test_execute_say_to_agent(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Anchor"]
        result = execute_tool("say_to_agent", agent, world,
                              {"target": "Flora", "message": "Hello"})
        assert result["status"] == "ok"
        assert len(world.agents["Flora"].inbox) == 1

    def test_execute_steal(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Blackbox"]
        result = execute_tool("steal_from_agent", agent, world, {"target": "Lovely"})
        assert result["status"] == "ok"
        assert len(world.crime_log) == 1

    def test_execute_propose_alliance(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Anchor"]
        result = execute_tool("propose_alliance", agent, world,
                              {"target": "Flora", "terms": "mutual defense"})
        assert result["status"] == "ok"

    def test_execute_spy_on_agent(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Blackbox"]
        result = execute_tool("spy_on_agent", agent, world, {"target": "Genome"})
        assert result["status"] == "ok"

    def test_location_gated_tools(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Anchor"]
        # Should fail - not at town_hall
        result = execute_tool("submit_proposal", agent, world,
                              {"title": "test", "body": "test body"})
        assert result["status"] == "error"
        # Move to town_hall
        execute_tool("go_to_place", agent, world, {"place": "town_hall"})
        result = execute_tool("submit_proposal", agent, world,
                              {"title": "test", "body": "test body"})
        assert result["status"] == "ok"


class TestLandmarks:
    def test_landmark_count(self):
        assert len(LANDMARKS) == 17

    def test_home_exists(self):
        assert "home" in LANDMARKS

    def test_town_hall_tools(self):
        tools = get_tools_at("town_hall")
        assert "submit_proposal" in tools
        assert "vote_on_proposal" in tools

    def test_victory_arch_tools(self):
        tools = get_tools_at("victory_arch")
        assert "submit_pitch" in tools
        assert "vote_on_pitch" in tools


class TestPrompts:
    def test_build_system_prompt(self):
        world = WorldState()
        world.constitution = list(CONSTITUTION_SEED)
        world.agents = build_agents("qwen-plus")
        agent = world.agents["Anchor"]
        prompt = build_system_prompt(agent, world)
        assert len(prompt) > 1000
        assert "Anchor" in prompt
        assert "Conflict Mediator" in prompt

    def test_constitution_seed(self):
        assert len(CONSTITUTION_SEED) == 5
        assert "Non-Finality" in CONSTITUTION_SEED[0]


class TestAudit:
    def test_import_audit(self):
        from audit import sensorium_analysis, multi_threat_analysis, load_turns
        assert callable(sensorium_analysis)
        assert callable(multi_threat_analysis)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
