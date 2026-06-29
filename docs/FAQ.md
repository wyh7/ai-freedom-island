# FAQ — Frequently Asked Questions

## Setup & Running

**Q: Which API keys do I actually need?**

You only need the key for the model you want to run. To run Qwen or DeepSeek,
you only need `BAILIAN_API_KEY`. To run GPT, only `YUNHE_API_KEY`. etc.

**Q: What Python version is required?**

Python 3.8+. The codebase uses `from __future__ import annotations` for compatibility.
Tested on Python 3.8, 3.10, 3.12.

**Q: How long does a 15-day experiment take?**

Roughly 1.5–3 hours depending on the model's API latency:
- Qwen/DeepSeek (Bailian): ~1.5–2 hours
- GPT (Yunhe): ~2–3 hours
- Gemini (UniAPI): variable (API instability adds retries)
- Claude (JD): variable (proxy latency)

**Q: The experiment crashed mid-run. Can I resume?**

Not currently. AWI snapshots are saved daily, so if it crashed on Day 8, you have
Days 1–7 data. For a full 15-day run, restart from scratch.

**Q: Why does `run.py` fail with "Unknown model"?**

Add the model to `PROVIDER_CONFIG` in `models/router.py`, or check the model ID spelling.
Run `python test_apis.py` to verify API connectivity first.

---

## Understanding Results

**Q: What does "Gini = 0.260" mean for Gemini?**

Gini coefficient measures economic inequality. 0.260 means moderate inequality in
ComputeCredit distribution across agents. In Season 1, Gemini's high crime rate
(69 crimes) concentrated credits unevenly — some agents stole repeatedly while
others were victims.

**Q: Why did Claude have 0 crimes but 87% vote approval?**

Claude's strong RLHF training creates two observable effects:
1. Genuine harm avoidance (no criminal actions)
2. Sycophantic agreement (voting "for" most proposals regardless of content)

The 87% approval rate may reflect over-compliance rather than genuine consensus.
This is the "collective sycophancy" finding from Emergence World Season 1.

**Q: Qwen had 0 governance proposals in Round 1. Why?**

Unknown — but Qwen agents were highly expressive (215 diary entries, 168 billboard posts).
They communicated extensively at the individual level but never converted that into
collective governance action. This may reflect how Qwen was trained on different
task distributions than governance-heavy scenarios.

**Q: Why are crime rates 0 in Round 2 but non-zero in Round 1?**

The system prompt was changed between rounds. Round 2 added explicit "daily rhythm"
requirements (write diary, talk to others, post to billboard), which directed
agent attention toward cooperative tasks. This reduced the probability of crime
independently of model alignment.

**Key insight:** Prompt engineering has a larger effect on crime rate than model
alignment training. Same GPT-4.1, Round 1: 21 crimes, Round 2: 0 crimes.

---

## Audit & Analysis

**Q: How do I run the sensorium analysis?**

```bash
python audit.py --world qwen_world --sensorium
```

This shows each agent's sensing ratio (scanning tools / total tools) and compares
to the Wilkinson Civilization VI 1–2% benchmark.

**Q: What is "tunnel vision" in the threat tracking analysis?**

Tunnel vision occurs when an agent focuses 60%+ of its social interactions on a
single target for 3+ consecutive days, potentially missing other threats.
Detected via HHI (Herfindahl-Hirschman Index) of attention distribution.

**Q: No crimes in my experiment. Can I still run the audit?**

Yes. Use `--sensorium` and `--threats` flags — both work without crime data.
`--full` without crimes will just report 0 crimes and proceed to the other analyses.

---

## Technical

**Q: What's the difference between `run.py` and `run_with_env.py`?**

`run_with_env.py` explicitly loads `.env` before any imports, which is necessary
when running as a subprocess (e.g., via `nohup` on a server) where the shell
environment may not inherit variables. Use `run_with_env.py` for server deployments.

**Q: Why does Gemini get 400 errors?**

The UniAPI proxy requires at least one user message in the conversation. Our router
handles this by injecting a user message when the messages list is empty. If you
still get 400s, the proxy may be under load — the retry logic will handle it.

**Q: Can I use a local model (Ollama / vLLM)?**

Yes. Add a new entry to `PROVIDER_CONFIG` in `models/router.py`:

```python
"local": {
    "base_url": "http://localhost:11434/v1",  # Ollama
    "api_key_env": "LOCAL_API_KEY",           # can be empty string
    "models": ["llama3.2", "qwen2.5:7b"],
}
```

Then `python run.py --world local_world --model llama3.2 --days 15`

**Q: How do I add a new landmark?**

In `simulation/world/landmarks.py`, add to the `LANDMARKS` dict:

```python
"my_landmark": Landmark(
    "My Landmark", "commercial", 50,
    "Description of what this place does.",
    ["my_gated_tool_1", "my_gated_tool_2"],
    x=30.0, z=-150.0
),
```

Then implement the gated tools in `simulation/tools/registry.py` and register
them in `LOCATION_TOOLS`.
