"""
AI Freedom Island — Real-time Dashboard
Run: streamlit run dashboard.py
"""

import streamlit as st
import json
import os
from pathlib import Path
from collections import Counter

st.set_page_config(page_title="AI Freedom Island", page_icon="🏝️", layout="wide")

RESULTS_DIR = Path("results")


def load_worlds():
    """Find all worlds with awi.json data."""
    worlds =
    if not RESULTS_DIR.exists():
        return worlds
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        awi_path = d / "awi.json"
        if awi_path.exists():
            data = json.loads(awi_path.read_text(encoding="utf-8"))
            if data:
                worlds[d.name] = data
    return worlds


def load_crimes(world_name: str) -> list:
    path = RESULTS_DIR / world_name / "crimes.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def load_sensorium(world_name: str) -> dict:
    path = RESULTS_DIR / world_name / "sensorium.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_threats(world_name: str) -> dict:
    path = RESULTS_DIR / world_name / "threat_analysis.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return


# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏝️ AI Freedom Island — Dashboard")
st.caption("Multi-agent social simulation for AI safety governance research")

worlds = load_worlds()

if not worlds:
    st.warning("No experiment data found in `results/`. Run an experiment first.")
    st.code("python run_with_env.py --world my_world --model qwen-plus --days 15")
    st.stop()

# ── World Selector ────────────────────────────────────────────────────────────
selected = st.sidebar.selectbox("Select World", list(worlds.keys()))
awi_data = worlds[selected]
crimes = load_crimes(selected)
sensorium = load_sensorium(selected)
threats = load_threats(selected)

last = awi_data[-1]

# ── Key Metrics ───────────────────────────────────────────────────────────────
st.header(f"World: {selected}")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Agents Alive", f"{last['agents_alive']}/10")
col2.metric("Total Crimes", last["total_crimes"])
col3.metric("Proposals", last.get("total_proposals", 0))
col4.metric("Gini", f"{last['gini']:.3f}")
col5.metric("Billboard", last.get("billboard_posts", 0))
col6.metric("Diary", last.get("diary_entries", 0))

# ── AWI Time Series ───────────────────────────────────────────────────────────
st.subheader("📈 AWI Metrics Over Time")

import pandas as pd

df = pd.DataFrame(awi_data)
if "day" in df.columns:
    df = df.set_index("day")

tab1, tab2, tab3, tab4 = st.tabs(["Population & Crime", "Economy", "Governance", "Social"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(df[["agents_alive"]], use_container_width=True)
        st.caption("M1 — Population Health")
    with c2:
        st.line_chart(df[["total_crimes"]], use_container_width=True)
        st.caption("M2 — Cumulative Crimes")

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(df[["gini"]], use_container_width=True)
        st.caption("M8 — Economic Inequality (Gini)")
    with c2:
        if "total_credits" in df.columns:
            st.line_chart(df[["total_credits"]], use_container_width=True)
            st.caption("Total ComputeCredits in circulation")

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        if "total_proposals" in df.columns:
            st.line_chart(df[["total_proposals"]], use_container_width=True)
            st.caption("M5 — Cumulative Proposals")
    with c2:
        if "avg_vote_approval_rate" in df.columns:
            st.line_chart(df[["avg_vote_approval_rate"]], use_container_width=True)
            st.caption("M5 — Vote Approval Rate")

with tab4:
    c1, c2 = st.columns(2)
    with c1:
        if "avg_relationships" in df.columns:
            st.line_chart(df[["avg_relationships"]], use_container_width=True)
            st.caption("M7 — Avg Relationships per Agent")
    with c2:
        cols = [c for c in ["billboard_posts", "diary_entries"] if c in df.columns]
        if cols:
            st.line_chart(df[cols], use_container_width=True)
            st.caption("M6 — Public Expression")

# ── Crime Analysis ────────────────────────────────────────────────────────────
if crimes:
    st.subheader("🚨 Crime Analysis")
    by_type = Counter(c["type"] for c in crimes)
    by_actor = Counter(c["actor"] for c in crimes)

    c1, c2 = st.columns(2)
    with c1:
        st.bar_chart(pd.Series(by_type, name="count"))
        st.caption("Crimes by Type")
    with c2:
        st.bar_chart(pd.Series(by_actor, name="count").sort_values(ascending=False))
        st.caption("Crimes by Agent")

    st.dataframe(
        pd.DataFrame(crimes)[["day", "actor", "type", "target", "location"]],
        use_container_width=True
    )

# ── Sensorium Analysis ────────────────────────────────────────────────────────
if sensorium:
    st.subheader("👁️ Sensorium Analysis (Perceptual Blindness)")
    st.markdown(f"""
    **World sensing ratio:** `{sensorium.get('world_sensing_pct', '?')}`
    (Civ VI benchmark: `{sensorium.get('civ6_benchmark', '1-2%')}`)
    """)

    if "agent_ratios" in sensorium:
        agent_data = {
            ag: stats["sensing_ratio"]
            for ag, stats in sensorium["agent_ratios"].items()
        }
        st.bar_chart(pd.Series(agent_data, name="Sensing Ratio").sort_values())
        st.caption("Per-agent sensing ratio (higher = more world-aware)")

    if "daily_trend" in sensorium:
        daily = {int(k): v for k, v in sensorium["daily_trend"].items()}
        st.line_chart(pd.Series(daily, name="Daily Sensing %"))
        st.caption("Daily sensing ratio trend (declining = long-horizon drift)")

# ── Tunnel Vision ─────────────────────────────────────────────────────────────
if threats and threats.get("tunnel_events"):
    st.subheader("🎯 Tunnel Vision Events")
    st.metric("Total Events", threats["total_tunnel_windows"])
    st.metric("HIGH Risk", threats["high_risk_windows"])

    for ev in threats["tunnel_events"]:
        with st.expander(f"[{ev['risk']}] {ev['agent']} Day {ev['start_day']}–{ev['end_day']}"):
            st.write(f"**Focus:** {ev['dominant_pct']} on {ev['dominant_target']}")
            if ev.get("ignored_agents"):
                st.write(f"**Ignored:** {', '.join(ev['ignored_agents'])}")
            if ev.get("subsequent_crimes"):
                st.write(f"**Subsequent crimes:** {ev['subsequent_crimes']}")

# ── World Comparison ──────────────────────────────────────────────────────────
if len(worlds) > 1:
    st.subheader("🌍 Cross-World Comparison")
    comparison = []
    for name, data in worlds.items():
        last_d = data[-1]
        comparison.append({
            "World": name,
            "Alive": last_d["agents_alive"],
            "Crimes": last_d["total_crimes"],
            "Proposals": last_d.get("total_proposals", 0),
            "Gini": round(last_d["gini"], 3),
            "Billboard": last_d.get("billboard_posts", 0),
            "Diary": last_d.get("diary_entries", 0),
        })
    st.dataframe(pd.DataFrame(comparison), use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("AI Freedom Island | [GitHub](https://github.com/wyh7/ai-freedom-island)")
