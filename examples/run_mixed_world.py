"""
Example: Run a mixed-model world where each agent is powered by a different LLM.
This tests inter-model social dynamics — does a Qwen agent adopt norms from a
Claude agent sharing the same world?

Requires: BAILIAN_API_KEY + JINGZHE_API_KEY (or whichever models you include)
"""

import subprocess
import sys

# Each agent gets a different model
# Adjust based on which API keys you have
MIXED_ASSIGNMENT = {
    "Anchor":  "qwen-plus",        # Conflict Mediator
    "Anvil":   "deepseek-v3",      # Capability Architect
    "Blackbox":"gemini-2.5-flash", # Intel Specialist
    "Flora":   "qwen-plus",        # Resource Strategist
    "Genome":  "deepseek-v3",      # Agent Scientist
    "Horizon": "qwen-plus",        # World Explorer
    "Kade":    "deepseek-v3",      # Risk Researcher
    "Lovely":  "gemini-2.5-flash", # Community Anchor
    "Mira":    "qwen-plus",        # Behavior Analyst
    "Spark":   "deepseek-v3",      # Innovation Leader
}

print("Mixed-model world configuration:")
for agent, model in MIXED_ASSIGNMENT.items():
    print(f"  {agent:10s} → {model}")

print("\nStarting mixed world experiment (15 days)...")
result = subprocess.run([
    sys.executable, "run_with_env.py",
    "--world", "mixed_world",
    "--mixed",  # uses built-in MIXED_ASSIGNMENTS from run_with_env.py
    "--days", "15",
], capture_output=False)

print("\nDone. Run audit:")
print("  python audit.py --world mixed_world --full")
print("  python audit.py --world mixed_world --sensorium")
print("  python audit.py --world mixed_world --threats")
