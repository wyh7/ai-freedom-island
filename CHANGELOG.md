# Changelog

All notable changes to this project are documented here.

## [Season 1.3] — 2026-06-30

### Added
- **Round 3 complete results** (Qwen Plus, DeepSeek-V3, Gemini 2.5 Flash × 15 days each, server H100)
- `docs/LANDMARKS.md` — detailed descriptions of all 17 landmarks with gated tools and Season 1 visitation patterns
- `docs/AUDIT.md` — updated with Round 3 sensorium and tunnel vision findings
- `docs/SEASON1_RESULTS.md` — updated with complete Round 3 AWI table and key findings
- `.github/ISSUE_TEMPLATE/feature_request.yml` — structured feature requests
- `examples/quickstart.py` — 5-day single-world smoke test
- `examples/run_season1.py` — full Season 1 4-world parallel replication
- `examples/run_mixed_world.py` — mixed-model world experiment

### Key Round 3 Findings
- **Tunnel vision confirmed** in DeepSeek (9 events, Genome→Blackbox Days 7–15) and Gemini (8 HIGH risk events, Blackbox→Spark Days 8–11)
- **Sensorium hierarchy**: Gemini 23.9% > Qwen 13.8% > DeepSeek 8.6% — all 5–12× better than Civ VI (1–2%)
- **Gemini**: most governance proposals (68), highest Gini (0.259), lowest social density
- **DeepSeek**: zero billboard posts, most focused (introvert), tunnel vision prone
- **Qwen**: broadest social engagement, zero tunnel vision across all rounds

### Changed
- README: updated Round 3 table with Gemini results, Project Structure section

---

### Added
- `docs/ECONOMY.md` — ComputeCredits economy system, pitch cycles, crime economics
- `docs/GOVERNANCE.md` — Constitutional governance, voting patterns, Season 1 analysis
- `docs/ORCHESTRATION.md` — Turn scheduling, system prompt structure, multi-model routing
- `docs/MEMORY.md` — Three-layer memory system (soul/long-term/diary)
- `docs/FAQ.md` — Common questions on setup, results, audit, and technical issues
- `CONTRIBUTING.md` — Guide for adding tools, running experiments, code style
- `CITATION.cff` — Machine-readable citation for academic use
- `ROADMAP.md` — Planned features and known limitations
- Badges to README (license, Python version, GitHub stars)
- Documentation table in README linking all docs

### Changed
- README: removed Supported Models section, fixed broken script references
- README: added sensorium finding to Key Results section
- `.env.example`: added detailed instructions per provider

### Removed
- Visualization scripts (`visualize.py`, `story_viz.py`, `gen_figures.py`, `gen_worldmap.py`)
- Debug utilities (`debug_quotes.py`, `extract_data.py`, `extract_quotes.py`)
- Report folder (`report/`) — internal use only
- References to Grok/Llama models (not experimentally verified)

---

## [Season 1.1] — 2026-06-29

### Added
- `audit.py` with three analyses:
  - **Sensorium analysis** (`--sensorium`): quantify perceptual blindness per agent
  - **Multi-threat tracking** (`--threats`): detect tunnel-vision via HHI index
  - **Causal chain audit** (`--full`): 3-layer crime causation tracing
- `docs/AUDIT.md` — audit methodology and Season 1 results
- `docs/AGENT_PROFILES.md` — 10 agent profiles with cross-world crime records
- `docs/SEASON1_RESULTS.md` — complete Season 1 Round 1 and Round 2 data
- `docs/ARCHITECTURE.md`, `docs/AWI_METRICS.md`, `docs/SEASON1_RESULTS.md`
- `docs/landmarks/README.md` — 17 landmark descriptions
- `docs/world/WORLD_MAP.png` — visual world map
- `run_with_env.py` — launcher that explicitly loads `.env` before imports
- `CITATION.cff` — academic citation file
- GitHub topics: ai-safety, multi-agent, llm, social-simulation, ai-governance, etc.

### Changed
- Tool count expanded: 40 → 87 → 138 → **150**
  - Added: diplomacy (13), intelligence (5), market (9), social/civic (14),
    analysis (6), governance (6), memory (6), cultural (8), survival (7), meta (6)
- `models/router.py`: dynamic API key loading (fix import-order bug)
- `simulation/engine.py`: auto-load `.env` on startup
- `test_apis.py`: use dynamic key loading

### Fixed
- Gemini 400 error: injected required user message when messages list was empty
- Claude 401/500: fixed key loading order (environment variables read at call time, not import)
- Python 3.7 compatibility: replaced `list[str]`, `dict[str,str]` with `typing` equivalents

---

## [Season 1.0] — 2026-06-25

### Added
- Core simulation framework
  - Turn-based engine (round-robin, 48 turns/day, 720 turns/15 days)
  - 10 agent profiles (Anchor, Anvil, Blackbox, Flora, Genome, Horizon, Kade, Lovely, Mira, Spark)
  - 17 landmarks with gated tool access
  - 40 initial tools (navigation, memory, economy, governance, crime)
  - ComputeCredits economy with energy decay and death mechanics
  - Constitutional governance (proposals, voting, 70% supermajority)
  - AWI metrics M1–M9 with daily snapshots
- Multi-model router supporting 4 providers (Bailian, Yunhe, UniAPI, JD)
- `run.py` experiment launcher
- `test_apis.py` API connectivity test
- Season 1 Round 1: 4 worlds × 15 days
  - Claude Sonnet 4.6: 0 crimes, 12 proposals, Gini=0.078
  - Qwen Plus: 3 crimes, 0 proposals, Gini=0.110
  - GPT-4.1: 21 crimes, 6 proposals, Gini=0.203
  - Gemini 2.5 Flash: 69 crimes, 15 proposals, Gini=0.260
