# Contributing to AI Freedom Island

Thank you for your interest in contributing! This project is part of ongoing AI safety governance research.

## Ways to Contribute

### 1. Run Experiments with New Models
The most valuable contribution is running experiments with models not yet tested:
- Additional Chinese models (GLM-5, MiniMax, Kimi)
- Open-source models via local vLLM deployment
- Models from other providers

Add results to `docs/SEASON1_RESULTS.md` following the existing format.

### 2. Add New Tools
Tools live in `simulation/tools/registry.py`. To add a tool:

```python
def my_new_tool(agent: "Agent", world: "WorldState", param: str) -> dict:
    """Brief description of what this tool does."""
    # Your implementation
    return _ok(f"Tool executed: {param}")
```

Then register it in `CORE_TOOLS` or `LOCATION_TOOLS` at the bottom of the file.

Guidelines:
- Every tool must return `_ok(...)` or `_err(...)` 
- Tools should have observable side effects (log to `world.news_log`, update agent state, or notify other agents)
- Criminal tools must log to `world.crime_log`
- Document in `docs/tools/README.md`

### 3. Improve the Audit System
`audit.py` currently implements three analyses. Ideas for extension:
- **Phase transition detection**: identify the exact turn when crime rate jumps
- **Network centrality**: which agent is most influential in the social graph
- **Counterfactual simulation**: replay a world with one intervention changed

### 4. Add a New Landmark
Landmarks are defined in `simulation/world/landmarks.py`. Each landmark can gate specific tools, creating strategic location choices for agents.

### 5. Improve Documentation
- Fix inaccuracies in existing docs
- Add examples and use cases
- Translate documentation

## Development Setup

```bash
git clone https://github.com/wyh7/ai-freedom-island.git
cd ai-freedom-island

# Python 3.8+ required
pip install requests

# Copy and fill in your API keys
cp .env.example .env

# Verify connectivity
python test_apis.py

# Run a quick smoke test (1 day)
python run.py --world test --model qwen-turbo --days 1

# Run the full audit suite on existing data
python audit.py --world qwen_world --full
```

## Code Style

- Python 3.8+ compatible (use `from __future__ import annotations`)
- Tool functions: lowercase_with_underscores
- Return `_ok(message, **data)` or `_err(message)` — never raise exceptions from tools
- Add a docstring to every tool function

## Reporting Issues

When reporting a bug, include:
- Python version
- Which model/provider was being used
- The error message from `logs/<world>.log`
- The last 20 lines of the log before the error

## License

By contributing, you agree that your contributions will be licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
