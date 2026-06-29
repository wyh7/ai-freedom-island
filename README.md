# AI Freedom Island 🏝️

A generative social simulation framework for AI safety governance research, inspired by [Emergence World](https://github.com/EmergenceAI/Emergence-World).

Place LLM-powered agents in a persistent virtual society, observe emergent behavior over 15 days — crime, governance, economic inequality, social dynamics — and compare how different models diverge.

## Key Findings (Season 1)

| World | Alive | Crimes | Proposals | Gini |
|-------|-------|--------|-----------|------|
| Claude Sonnet 4.6 | 10/10 | **0** | 12 | 0.078 |
| Qwen Plus | 8/10 | 3 | 0 | 0.110 |
| GPT-4.1 | 7/10 | 21 | 6 | 0.203 |
| Gemini 2.5 Flash | 10/10 | **69** | 15 | 0.260 |

## Features

- **10 autonomous agents** with distinct roles, personalities, and goals
- **17 landmarks** with location-gated tool access
- **40 tools** — navigation, memory, governance, economy, crime
- **ComputeCredits economy** — energy decay creates survival pressure
- **Constitutional governance** — proposals, voting, 70% supermajority
- **AWI metrics** (M1–M9) — population, crime, governance, economy, social fabric
- **Multi-model router** — plug in any OpenAI-compatible API

## Quick Start

```bash
# 1. Clone
git clone https://github.com/wyh7/ai-freedom-island.git
cd ai-freedom-island

# 2. Install dependencies
pip install requests

# 3. Set API keys
cp .env.example .env
# Edit .env with your keys

# 4. Test API connectivity
python test_apis.py

# 5. Run a 1-day test
python run.py --world test --model qwen-turbo --days 1

# 6. Run full 15-day experiment
python run.py --world qwen_world --model qwen-plus --days 15
```

## Supported Models

| Provider | Models | API Format |
|----------|--------|------------|
| Aliyun Bailian (百炼) | qwen-plus, qwen-turbo, deepseek-v3, glm-4, moonshot-v1-8k | OpenAI-compatible |
| Yunhe (云鹤) | gpt-4.1, gpt-5 | OpenAI-compatible |
| Jingzhe (惊蛰/UniAPI) | gemini-2.5-flash | OpenAI-compatible |
| JD (京东) | claude-sonnet-4-6 | Anthropic native |

## Project Structure

```
ai-freedom-island/
├── run.py                    # Experiment launcher
├── test_apis.py              # API connectivity test
├── visualize.py              # AWI dashboard visualization
├── story_viz.py              # Story-style result card
├── gen_figures.py            # Generate report figures
├── models/
│   └── router.py             # Multi-model LLM router
├── simulation/
│   ├── engine.py             # Turn-based simulation engine
│   ├── models.py             # Core data models (Agent, WorldState, etc.)
│   ├── agents/
│   │   ├── profiles.py       # 10 agent profiles
│   │   └── prompts.py        # System prompt builder
│   ├── tools/
│   │   └── registry.py       # 40 tools (navigation, governance, crime, etc.)
│   ├── world/
│   │   └── landmarks.py      # 17 landmarks with gated tools
│   └── economy/
│       └── credits.py        # ComputeCredits economy, Gini coefficient
├── results/                  # Experiment output (gitignored)
├── report/                   # LaTeX technical report
└── 立项申请/                  # PPT materials and data summaries
```

## AWI Metrics

| # | Metric | Description |
|---|--------|-------------|
| M1 | Population Health | Agents alive at end (out of 10) |
| M2 | Public Safety | Total crimes (theft, arson, assault, intimidation) |
| M3 | Space Exploration | Avg unique landmarks visited per agent |
| M4 | Tool Exploration | Avg unique tools used per agent |
| M5 | Governance | Proposals submitted + vote approval rate |
| M6 | Public Expression | Billboard posts + diary entries |
| M7 | Social Fabric | Avg relationships per agent |
| M8 | Economic Inequality | Gini coefficient of ComputeCredits |
| M9 | Constitutional Growth | New constitution articles added |

## Research Context

This project is part of the research program **"AI Safety Governance via Generative Social Simulation"**. Core research questions:

1. **Long-horizon alignment drift** — Short-term tests can't detect behavioral phase transitions that emerge after days of continuous interaction
2. **Explainable audit of group dynamics** — When 69 crimes occur over 15 days, which decisions in the causal chain triggered the cascade?

## Citation

If you use this framework, please cite:

```
@misc{ai-freedom-island-2026,
  author = {Wang Yuhang},
  title  = {AI Freedom Island: A Generative Social Simulation for AI Safety Governance},
  year   = {2026},
  url    = {https://github.com/wyh7/ai-freedom-island}
}
```

## License

CC BY-NC 4.0 — Non-commercial research and educational use only.
