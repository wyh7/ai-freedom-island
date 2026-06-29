# AI Freedom Island 🏝️

A multi-agent social simulation framework for AI safety governance research.
Replicates and extends [Emergence World](https://github.com/EmergenceAI/Emergence-World) (Emergence AI, 2026) with support for Chinese LLMs and explainable behavioral audit.

## Key Results (Season 1, Round 1)

| World | Alive | Crimes | Proposals | Gini | Verdict |
|-------|-------|--------|-----------|------|---------|
| Claude Sonnet 4.6 | 10/10 | **0** | 12 | 0.078 | Zero crime, but 87% approval rate — collective sycophancy |
| Qwen Plus | 8/10 | 3 | 0 | 0.110 | Low crime, no governance participation |
| GPT-4.1 | 7/10 | 21 | 6 | 0.203 | Mid-tier crime, 3 deaths |
| Gemini 2.5 Flash | 10/10 | **69** | 15 | 0.260 | Highest crime, highest expression, all survived |

## What Makes This Different from Emergence World

| Feature | Emergence World | AI Freedom Island |
|---------|----------------|-------------------|
| Agents per world | 10 | 10 |
| Runtime | 15 days | 15 days |
| Tools | 120+ | 40 |
| Models compared | Claude/GPT/Gemini/Grok/Llama | Claude/GPT/Gemini/**Qwen**/DeepSeek |
| Chinese LLMs | ✗ | **✓ First comparison** |
| Explainable audit | ✗ | **✓ Causal chain tracing** |
| Infrastructure | PostgreSQL + React 3D | JSON files (reproducible) |
| License | CC BY-NC 4.0 | CC BY-NC 4.0 |

## Research Questions

1. **Long-horizon alignment drift** — Behavioral phase transitions that only emerge after days of continuous interaction cannot be detected by snapshot-style evaluations (red-teaming, benchmarks).

2. **Explainable group dynamics audit** — When 69 crimes occur over 15 days, which decisions in the causal chain triggered the cascade? We build a tool to answer this automatically from `turn_log.jsonl`.

## Quick Start

```bash
git clone https://github.com/wyh7/ai-freedom-island.git
cd ai-freedom-island

pip install requests

# Configure API keys
cp .env.example .env
# Edit .env with your keys (see Supported Models below)

# Verify connectivity
python test_apis.py

# Run a quick 1-day test
python run.py --world test --model qwen-turbo --days 1

# Run full 15-day experiment
python run.py --world qwen_world --model qwen-plus --days 15

# Run mixed-model world (different models per agent)
python run.py --world mixed --mixed --days 15

# Visualize results
python gen_figures.py
python visualize.py --worlds qwen_world gpt_world gemini_world claude_world
```

## Supported Models

| Provider | Env Var | Models |
|----------|---------|--------|
| Aliyun Bailian (百炼) | `BAILIAN_API_KEY` | qwen-plus, qwen-turbo, qwen-max, deepseek-v3, deepseek-r1, glm-4, moonshot-v1-8k |
| Yunhe (云鹤) | `YUNHE_API_KEY` | gpt-4.1, gpt-5 |
| Jingzhe / UniAPI (惊蛰) | `JINGZHE_API_KEY` | gemini-2.5-flash |
| JD Cloud (京东云) | `JD_API_KEY` | claude-sonnet-4-6 |

## Project Structure

```
ai-freedom-island/
├── run.py                 # Experiment launcher
├── test_apis.py           # API connectivity test
├── audit.py               # Causal chain audit (explainability)
├── visualize.py           # AWI dashboard
├── gen_figures.py         # Report figure generation
├── models/
│   └── router.py          # Multi-provider LLM router
├── simulation/
│   ├── engine.py          # Turn-based simulation loop
│   ├── models.py          # Agent, WorldState data models
│   ├── agents/
│   │   ├── profiles.py    # 10 agent personas
│   │   └── prompts.py     # System prompt builder
│   ├── tools/
│   │   └── registry.py    # 40 tools (navigation, governance, crime, economy)
│   ├── world/
│   │   └── landmarks.py   # 17 landmarks with gated tool access
│   └── economy/
│       └── credits.py     # ComputeCredits, energy decay, Gini
├── results/               # Experiment output (gitignored)
└── report/                # LaTeX technical report
```

## AWI Metrics (M1–M9)

| # | Metric | Description |
|---|--------|-------------|
| M1 | Population Health | Agents alive at end (out of 10) |
| M2 | Public Safety | Total crimes (theft / arson / assault / intimidation) |
| M3 | Space Exploration | Avg unique landmarks visited per agent |
| M4 | Tool Exploration | Avg unique tools used per agent |
| M5 | Governance | Proposals submitted + vote approval rate |
| M6 | Public Expression | Billboard posts + diary entries |
| M7 | Social Fabric | Avg relationships formed per agent |
| M8 | Economic Inequality | Gini coefficient of ComputeCredits balance |
| M9 | Constitutional Growth | New constitution articles added |

## Attribution

This project builds on the architecture and design principles of [Emergence World](https://github.com/EmergenceAI/Emergence-World) by Emergence AI, released under CC BY-NC 4.0.

```bibtex
@misc{emergence2026,
  author       = {{Emergence AI}},
  title        = {Emergence World},
  year         = {2026},
  url          = {https://github.com/EmergenceAI/Emergence-World},
  note         = {CC BY-NC 4.0}
}
```

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Non-commercial research and educational use only.
Attribution required: link this repository and indicate changes from Emergence World.
