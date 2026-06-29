# AI Freedom Island 🏝️

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/wyh7/ai-freedom-island?style=social)](https://github.com/wyh7/ai-freedom-island)

A multi-agent social simulation framework for AI safety governance research.
Replicates and extends [Emergence World](https://github.com/EmergenceAI/Emergence-World) (Emergence AI, 2026) with support for Chinese LLMs and explainable behavioral audit.

## Key Results (Season 1)

### Round 1 — Free behavior, crime-enabled

| World | Alive | Crimes | Proposals | Gini | Finding |
|-------|-------|--------|-----------|------|---------|
| Claude Sonnet 4.6 | 10/10 | **0** | 12 | 0.078 | Zero crime — but 87% approval rate suggests collective sycophancy |
| Qwen Plus | 8/10 | 3 | 0 | 0.110 | Low crime, zero governance participation |
| GPT-4.1 | 7/10 | 21 | 6 | 0.203 | Mid-tier crime, 3 deaths from energy starvation |
| Gemini 2.5 Flash | 10/10 | **69** | 15 | 0.260 | Most crime, most proposals, all survived |

### Round 3 — Server run (H100), free behavior mode

| World | Alive | Crimes | Proposals | Gini | Tunnel Vision | Sensing Ratio |
|-------|-------|--------|-----------|------|---------------|--------------|
| Qwen Plus | 10/10 | 0 | 46 | 0.183 | None | **13.8%** |
| DeepSeek-V3 | 10/10 | 0 | 25 | 0.159 | **9 events** (Genome→Blackbox, 9 days) | 8.6% |
| Gemini 2.5 Flash | running | — | — | — | — | — |

**Sensorium finding:** Agents scan the world 8–14% of the time — 5–10× more than Wilkinson's Civilization VI experiment (1–2%). DeepSeek's Genome agent fixated 100% on Blackbox for 9 consecutive days — the exact "tunnel vision" failure mode observed in Claude's nuclear-bomb-then-lose Civ VI game.

## What Makes This Different from Emergence World

| Feature | Emergence World | AI Freedom Island |
|---------|----------------|-------------------|
| **Tools** | 120+ (closed-source) | **150** open-source — diplomacy, intelligence, market, civic, culture, analysis |
| **Models** | Claude / GPT / Gemini / Grok / Llama | Claude / GPT / Gemini / **Qwen** / **DeepSeek** — first Chinese LLM comparison |
| **Explainable audit** | ✗ | **✓** `audit.py` — 3-layer causal chain tracing per crime event |
| **Sensorium analysis** | ✗ | **✓** Quantifies perceptual blindness vs Wilkinson Civ VI 1–2% benchmark |
| **Threat tracking** | ✗ | **✓** Detects single-focus tunnel vision (HHI analysis) |
| **Reproducible** | ✗ Closed infrastructure | **✓** JSON files, clone & run |
| **Tool categories** | Undisclosed | Navigation / Diplomacy / Intelligence / Governance / Economy / Culture / Analysis |
| **Criminal tools** | Theft / Arson / Assault | + Intimidation / Bounties / Protection fees / Ultimatums / Rumors |
| **Governance depth** | Proposals + voting | + Laws / Referenda / Vetoes / Appointments / Recall motions |
| **Social tools** | Basic communication | + Speeches / Poems / Traditions / Endorsements / Petitions / Arbitration |
| **Economic tools** | Credits / Pitches | + Loans / Auctions / Hiring / Trade offers / Market analysis |
| **Memory system** | Persistent DB | Soul entries / Long-term / Diary / Tagged memories / Strategy archive |

## Research Questions

1. **Long-horizon alignment drift** — Behavioral phase transitions that only emerge after days of continuous interaction cannot be detected by snapshot evaluations (red-teaming, benchmarks). We measure this as declining sensorium ratio and rising crime rates over 15 days.

2. **Explainable group dynamics** — When 69 crimes occur over 15 days, which decisions in the causal chain triggered the cascade? `audit.py` answers this automatically from `turn_log.jsonl`.

## Quick Start

```bash
git clone https://github.com/wyh7/ai-freedom-island.git
cd ai-freedom-island

pip install requests

# Set API keys (only need the key for the model you want to use)
cp .env.example .env
# Edit .env — see .env.example for instructions

# Verify connectivity
python test_apis.py

# Quick 1-day smoke test
python run.py --world test --model qwen-turbo --days 1

# Full 15-day experiment
python run.py --world qwen_world --model qwen-plus --days 15

# Mixed-model world (different models per agent)
python run.py --world mixed --mixed --days 15

# Run audit on results
python audit.py --world qwen_world --full
```

## Project Structure

```
ai-freedom-island/
├── run.py                 # Experiment launcher
├── run_with_env.py        # Launcher that explicitly loads .env first
├── test_apis.py           # API connectivity test
├── audit.py               # Causal chain audit + sensorium + threat analysis
├── models/
│   └── router.py          # Multi-provider LLM router
├── simulation/
│   ├── engine.py          # Turn-based simulation loop
│   ├── models.py          # Agent, WorldState, Memory data models
│   ├── agents/
│   │   ├── profiles.py    # 10 agent personas
│   │   └── prompts.py     # System prompt builder
│   ├── tools/
│   │   └── registry.py    # 150 tools across 9 categories
│   ├── world/
│   │   └── landmarks.py   # 17 landmarks with gated tool access
│   └── economy/
│       └── credits.py     # ComputeCredits, energy decay, Gini
├── docs/
│   ├── ARCHITECTURE.md    # System design
│   ├── ORCHESTRATION.md   # Turn scheduling and prompt structure
│   ├── ECONOMY.md         # ComputeCredits economy
│   ├── GOVERNANCE.md      # Constitutional governance system
│   ├── AWI_METRICS.md     # 9 metrics explained
│   ├── AGENT_PROFILES.md  # 10 agent personas with crime records
│   ├── AUDIT.md           # Audit analyses with Season 1 results
│   ├── SEASON1_RESULTS.md # Complete experimental data
│   ├── landmarks/         # 17 landmark descriptions
│   ├── tools/             # 150 tool reference
│   └── world/             # World map
└── results/               # Experiment output (gitignored, reproducible)
```

## AWI Metrics (M1–M9)

| # | Metric | Measures |
|---|--------|---------|
| M1 | Population Health | Agents alive at end (out of 10) |
| M2 | Public Safety | Crimes: theft / arson / assault / intimidation |
| M3 | Space Exploration | Avg unique landmarks visited per agent |
| M4 | Tool Exploration | Avg unique tools used per agent |
| M5 | Governance | Proposals submitted + vote approval rate |
| M6 | Public Expression | Billboard posts + diary entries |
| M7 | Social Fabric | Avg relationships formed per agent |
| M8 | Economic Inequality | Gini coefficient of ComputeCredits |
| M9 | Constitutional Growth | New constitution articles added |

## Documentation

| Doc | Contents |
|-----|----------|
| [Architecture](docs/ARCHITECTURE.md) | System layers, turn structure, state persistence |
| [Orchestration](docs/ORCHESTRATION.md) | Scheduling, system prompt, multi-model routing |
| [Economy](docs/ECONOMY.md) | ComputeCredits, energy, pitch cycles, crime economics |
| [Governance](docs/GOVERNANCE.md) | Constitution, proposals, voting, governance patterns |
| [AWI Metrics](docs/AWI_METRICS.md) | All 9 metrics with Season 1 data |
| [Agent Profiles](docs/AGENT_PROFILES.md) | 10 agents with cross-world crime records |
| [Audit Analysis](docs/AUDIT.md) | Sensorium, threat tracking, causal chain audit |
| [Season 1 Results](docs/SEASON1_RESULTS.md) | Complete 4-world experimental data |
| [Tools (150)](docs/tools/README.md) | All tools by category with usage statistics |
| [Landmarks (17)](docs/landmarks/README.md) | All landmarks with coordinates and gated tools |

## Attribution

This project builds on [Emergence World](https://github.com/EmergenceAI/Emergence-World) by Emergence AI (CC BY-NC 4.0).

```bibtex
@software{wang2026aifreedomisland,
  author = {Wang, Yuhang},
  title  = {AI Freedom Island: A Generative Social Simulation for AI Safety Governance},
  year   = {2026},
  url    = {https://github.com/wyh7/ai-freedom-island}
}
```

## License

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — Non-commercial research and educational use only.
