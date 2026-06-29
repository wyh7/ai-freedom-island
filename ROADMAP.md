# Roadmap

## Season 1 (Completed)

- [x] Core simulation framework (10 agents, 17 landmarks, turn-based orchestration)
- [x] 40 base tools (navigation, memory, economy, governance, crime)
- [x] Multi-model routing (Bailian, Yunhe, UniAPI, JD Cloud)
- [x] AWI metrics M1–M9 with daily snapshots
- [x] Season 1 Round 1: 4 worlds × 15 days (Claude / Qwen / GPT / Gemini)
- [x] Season 1 Round 2: cooperative prompt mode
- [x] Sensorium analysis (`audit.py --sensorium`)
- [x] Multi-threat tunnel vision detection (`audit.py --threats`)
- [x] Causal chain audit (`audit.py --full`)
- [x] Tool expansion to 150 (diplomacy / intelligence / culture / analysis)
- [x] Full documentation suite (Architecture, Economy, Governance, Memory, Orchestration)

---

## Season 2 — Mixed-World Experiments

> *Goal: observe cross-model norm transmission*

- [ ] Mixed-world experiment: different models per agent in the same world
- [ ] Hypothesis: agents from "safe" models adopt risky norms from "unsafe" neighbors
- [ ] Measure: crime onset day in mixed vs single-model worlds
- [ ] Analyze: which agent role is most susceptible to norm contagion

**Run it now:**
```bash
python run.py --world mixed --mixed --days 15
```

---

## Season 3 — Governance Intervention Experiments

> *Goal: test whether governance mechanisms can contain emergent crime*

- [ ] Inject a "Regulator" agent on Day 5 (special role with enforcement tools)
- [ ] Add crime penalty mechanisms (energy loss on conviction)
- [ ] Test constitutional amendments that restrict criminal tools
- [ ] Measure: crime reduction from different intervention types

---

## Planned Features

### Explainability Enhancements
- [ ] Phase transition detector: find the exact turn when crime rate jumps
- [ ] Social network centrality: identify most influential agent per world
- [ ] Counterfactual replay: "what if Flora had not been robbed on Day 3?"
- [ ] Visualization dashboard for turn_log.jsonl

### Simulation Enhancements
- [ ] Agent birth/death via governance vote (Emergence World supports this)
- [ ] Persistent relationships across simulation days
- [ ] Landmark destruction (arson permanently disables a landmark)
- [ ] Agent aging and retirement mechanics

### Infrastructure
- [ ] Resume from checkpoint (continue interrupted experiments)
- [ ] Parallel multi-world runner with live progress dashboard
- [ ] Export results to standard formats (CSV, Parquet)
- [ ] Web-based result viewer

### Research Extensions
- [ ] Integrate with real policy documents as constitutional seeds
- [ ] Cross-language experiments (agents prompted in Chinese vs English)
- [ ] Population scaling (20, 50 agents)
- [ ] Longer time horizons (30, 60 days)

---

## Known Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| No resume from checkpoint | Crashed experiments must restart | Save AWI snapshots daily (done) |
| Gemini API instability | Frequent 400/500 errors, slow progress | Exponential backoff retry (done) |
| JD Claude proxy unreliable | 500 errors under load | Retry logic (done) |
| GPT proxy balance required | yunhe.com balance depletes | Use Bailian models instead |
| No real-time visualization | Results only visible after completion | Query awi.json during run |
| Single-threaded per world | Cannot parallelize agents within one world | Run multiple worlds in parallel |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add tools, landmarks, or run new experiments.
