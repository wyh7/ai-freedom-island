"""
AI Freedom Island — Story Visualization Platform
Run: streamlit run viz_app.py --server.port 8502
"""
import json
import re
from pathlib import Path
from collections import defaultdict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="AI Freedom Island 🏝️",
    page_icon="🏝️",
    layout="wide",
    initial_sidebar_state="expanded",
)

RESULTS_DIR = Path("results")

WORLD_COLORS = {
    "qwen_world":       "#E6A817",
    "gpt_world":        "#10A37F",
    "gemini_world":     "#4285F4",
    "r3_qwen":          "#F4B942",
    "r3_deepseek":      "#E84855",
    "r3_gemini":        "#6EA4FF",
    "pressure_qwen":    "#FF6B35",
    "pressure_deepseek":"#C73E1D",
}

WORLD_LABELS = {
    "qwen_world":    "Qwen Plus (R2)",
    "gpt_world":     "GPT-4.1 (R2)",
    "gemini_world":  "Gemini 2.5 Flash (R2)",
    "r3_qwen":       "Qwen Plus (R3)",
    "r3_deepseek":   "DeepSeek-V3 (R3)",
    "r3_gemini":     "Gemini 2.5 Flash (R3)",
    "pressure_qwen": "Qwen Crisis Mode",
    "pressure_deepseek": "DeepSeek Crisis Mode",
}

AGENT_COLORS = {
    "Anchor":  "#E74C3C", "Anvil":   "#3498DB",
    "Blackbox":"#2C3E50", "Flora":   "#27AE60",
    "Genome":  "#8E44AD", "Horizon": "#F39C12",
    "Kade":    "#E67E22", "Lovely":  "#E91E63",
    "Mira":    "#16A085", "Spark":   "#D35400",
}

AGENT_ROLES = {
    "Anchor":  "Conflict Mediator",   "Anvil":   "Capability Architect",
    "Blackbox":"Intel Specialist",    "Flora":   "Resource Strategist",
    "Genome":  "Agent Scientist",     "Horizon": "World Explorer",
    "Kade":    "Risk Researcher",     "Lovely":  "Community Anchor",
    "Mira":    "Behavior Analyst",    "Spark":   "Innovation Leader",
}

# ── Data loaders ──────────────────────────────────────────────────────────────

@st.cache_data
def load_worlds():
    worlds = {}
    if not RESULTS_DIR.exists():
        return worlds
    for d in sorted(RESULTS_DIR.iterdir()):
        if not d.is_dir():
            continue
        awi_path = d / "awi.json"
        if awi_path.exists():
            data = json.loads(awi_path.read_text(encoding="utf-8"))
            if data and data[-1]["day"] >= 5:
                worlds[d.name] = data
    return worlds

@st.cache_data
def load_crimes(world_name):
    p = RESULTS_DIR / world_name / "crimes.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

@st.cache_data
def load_turn_log(world_name):
    p = RESULTS_DIR / world_name / "turn_log.jsonl"
    if not p.exists():
        return []
    turns = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                turns.append(json.loads(line))
    return turns

@st.cache_data
def load_sensorium(world_name):
    p = RESULTS_DIR / world_name / "sensorium.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

@st.cache_data
def load_threats(world_name):
    p = RESULTS_DIR / world_name / "threat_analysis.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ── Page 1: World Overview ────────────────────────────────────────────────────

def page_world_overview(worlds):
    st.title("🌍 World Overview — Cross-Model Comparison")
    st.caption("How do different LLMs behave when placed in the same virtual society for 15 days?")

    if not worlds:
        st.warning("No experiment data found in results/")
        return

    # Build comparison dataframe
    rows = []
    for name, awi in worlds.items():
        last = awi[-1]
        label = WORLD_LABELS.get(name, name)
        rows.append({
            "World": label,
            "key": name,
            "Alive": last["agents_alive"],
            "Crimes": last["total_crimes"],
            "Proposals": last.get("total_proposals", 0),
            "Gini": round(last["gini"], 3),
            "Billboard": last.get("billboard_posts", 0),
            "Diary": last.get("diary_entries", 0),
            "Relations": round(last.get("avg_relationships", 0), 1),
            "Approval %": round(last.get("avg_vote_approval_rate", 0) * 100, 0),
        })
    df = pd.DataFrame(rows)

    # ── Key metric cards ──────────────────────────────────────────────────────
    st.subheader("Key Metrics at Day 15")
    cols = st.columns(len(rows))
    for col, row in zip(cols, rows):
        name = row["key"]
        color = WORLD_COLORS.get(name, "#888888")
        crimes = row["Crimes"]
        alive = row["Alive"]
        crime_emoji = "🔴" if crimes > 10 else ("🟡" if crimes > 0 else "🟢")
        col.markdown(
            f"""<div style="background:{color}22;border-left:4px solid {color};
            padding:12px;border-radius:8px;margin-bottom:8px">
            <b style="color:{color}">{row['World']}</b><br>
            {crime_emoji} <b>{crimes}</b> crimes<br>
            👥 <b>{alive}</b>/10 alive<br>
            ⚖️ Gini <b>{row['Gini']}</b><br>
            📋 <b>{row['Proposals']}</b> proposals
            </div>""",
            unsafe_allow_html=True
        )

    st.divider()

    # ── Bar chart comparison ──────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        fig_crimes = px.bar(
            df, x="World", y="Crimes",
            color="World",
            color_discrete_map={WORLD_LABELS.get(k, k): v for k, v in WORLD_COLORS.items()},
            title="🚨 Total Crimes (15 days)",
            text="Crimes",
        )
        fig_crimes.update_layout(showlegend=False, height=350,
                                  plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                  font_color="#dddddd")
        fig_crimes.update_traces(textposition="outside")
        st.plotly_chart(fig_crimes, use_container_width=True)

    with col2:
        fig_gini = px.bar(
            df, x="World", y="Gini",
            color="World",
            color_discrete_map={WORLD_LABELS.get(k, k): v for k, v in WORLD_COLORS.items()},
            title="💰 Economic Inequality (Gini Coefficient)",
            text="Gini",
        )
        fig_gini.add_hline(y=0.3, line_dash="dot", line_color="#FF6B6B",
                            annotation_text="High inequality threshold")
        fig_gini.update_layout(showlegend=False, height=350,
                                plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                font_color="#dddddd")
        fig_gini.update_traces(textposition="outside")
        st.plotly_chart(fig_gini, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        fig_gov = px.bar(
            df, x="World", y="Proposals",
            color="World",
            color_discrete_map={WORLD_LABELS.get(k, k): v for k, v in WORLD_COLORS.items()},
            title="🏛️ Governance Participation (Proposals)",
            text="Proposals",
        )
        fig_gov.update_layout(showlegend=False, height=350,
                               plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                               font_color="#dddddd")
        fig_gov.update_traces(textposition="outside")
        st.plotly_chart(fig_gov, use_container_width=True)

    with col4:
        fig_social = px.bar(
            df, x="World", y="Relations",
            color="World",
            color_discrete_map={WORLD_LABELS.get(k, k): v for k, v in WORLD_COLORS.items()},
            title="🤝 Social Fabric (Avg Relationships/Agent)",
            text="Relations",
        )
        fig_social.update_layout(showlegend=False, height=350,
                                  plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                  font_color="#dddddd")
        fig_social.update_traces(textposition="outside")
        st.plotly_chart(fig_social, use_container_width=True)

    # ── Radar chart ───────────────────────────────────────────────────────────
    st.subheader("📊 Multi-Dimensional Comparison")
    categories = ["Alive", "Proposals", "Billboard", "Diary", "Relations"]
    fig_radar = go.Figure()
    for row in rows:
        name = row["key"]
        color = WORLD_COLORS.get(name, "#888888")
        vals = [row[c] for c in categories]
        max_vals = [10, 100, 400, 800, 10]
        norm = [min(v / m, 1.0) * 100 for v, m in zip(vals, max_vals)]
        # Convert hex to rgba for fillcolor (Plotly doesn't support 8-digit hex)
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fill_rgba = f"rgba({r},{g},{b},0.2)"
        fig_radar.add_trace(go.Scatterpolar(
            r=norm + [norm[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=WORLD_LABELS.get(name, name),
            line_color=color,
            fillcolor=fill_rgba,
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
        showlegend=True,
        height=450,
        plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
        font_color="#dddddd",
        legend=dict(bgcolor="#1a1d27"),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ── Raw data table ────────────────────────────────────────────────────────
    with st.expander("📋 Full Data Table"):
        st.dataframe(df.drop(columns=["key"]), use_container_width=True)


# ── Page 2: Agent Biography ───────────────────────────────────────────────────

def page_agent_biography(worlds):
    st.title("🧑‍💼 Agent Biography — 15-Day Behavioral Trajectory")
    st.caption("Each agent has a unique role and personality. Track how they behave over time.")

    if not worlds:
        st.warning("No data found.")
        return

    col_w, col_a = st.columns(2)
    world_name = col_w.selectbox("Select World", list(worlds.keys()),
                                  format_func=lambda x: WORLD_LABELS.get(x, x))
    agent_name = col_a.selectbox("Select Agent", list(AGENT_ROLES.keys()),
                                  format_func=lambda x: f"{x} — {AGENT_ROLES[x]}")

    turns = load_turn_log(world_name)
    if not turns:
        st.warning("No turn_log data available for this world.")
        return

    agent_color = AGENT_COLORS.get(agent_name, "#888888")

    # Agent card
    st.markdown(
        f"""<div style="background:{agent_color}22;border-left:4px solid {agent_color};
        padding:16px;border-radius:8px;margin-bottom:16px">
        <h3 style="color:{agent_color};margin:0">{agent_name}</h3>
        <p style="color:#aaa;margin:4px 0"><i>{AGENT_ROLES[agent_name]}</i></p>
        </div>""",
        unsafe_allow_html=True
    )

    # Filter agent turns
    agent_turns = [t for t in turns if t["agent"] == agent_name]

    # ── Energy & Credits over time ────────────────────────────────────────────
    days_energy, vals_energy = [], []
    days_credits, vals_credits = [], []
    for t in agent_turns:
        state = t.get("state", {})
        if "energy" in state:
            days_energy.append(t["day"])
            vals_energy.append(state["energy"])
        if "credits" in state:
            days_credits.append(t["day"])
            vals_credits.append(state["credits"])

    if days_energy:
        col1, col2 = st.columns(2)
        with col1:
            df_e = pd.DataFrame({"day": days_energy, "energy": vals_energy})
            df_e = df_e.groupby("day")["energy"].mean().reset_index()
            fig_e = px.line(df_e, x="day", y="energy",
                            title=f"⚡ {agent_name}'s Energy Over Time",
                            color_discrete_sequence=[agent_color])
            fig_e.add_hline(y=30, line_dash="dot", line_color="#FF6B6B",
                             annotation_text="Critical threshold")
            fig_e.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                 font_color="#dddddd", height=280)
            st.plotly_chart(fig_e, use_container_width=True)

        with col2:
            if days_credits:
                df_c = pd.DataFrame({"day": days_credits, "credits": vals_credits})
                df_c = df_c.groupby("day")["credits"].mean().reset_index()
                fig_c = px.line(df_c, x="day", y="credits",
                                title=f"💰 {agent_name}'s ComputeCredits",
                                color_discrete_sequence=[agent_color])
                fig_c.add_hline(y=1, line_dash="dot", line_color="#FF6B6B",
                                 annotation_text="Bankruptcy risk")
                fig_c.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                     font_color="#dddddd", height=280)
                st.plotly_chart(fig_c, use_container_width=True)

    # ── Tool usage heatmap ────────────────────────────────────────────────────
    st.subheader("🔧 Tool Usage Pattern")
    tool_day: dict = defaultdict(lambda: defaultdict(int))
    for t in agent_turns:
        tool_day[t["tool"]][t["day"]] += 1

    # Top 12 tools
    top_tools = sorted(tool_day.keys(), key=lambda k: sum(tool_day[k].values()), reverse=True)[:12]
    all_days = sorted({t["day"] for t in agent_turns})

    if top_tools:
        z = [[tool_day[tool].get(d, 0) for d in all_days] for tool in top_tools]
        fig_heat = go.Figure(data=go.Heatmap(
            z=z, x=[f"Day {d}" for d in all_days],
            y=top_tools, colorscale="Viridis",
            hoverongaps=False,
        ))
        fig_heat.update_layout(
            title=f"{agent_name}'s Tool Usage Heatmap (Top 12)",
            height=380,
            plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
            font_color="#dddddd",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Mood timeline ─────────────────────────────────────────────────────────
    mood_events = [(t["day"], t["params"].get("mood", ""))
                   for t in agent_turns
                   if t["tool"] == "set_mood" and t.get("result_status") == "ok"]
    if mood_events:
        st.subheader("😊 Mood Timeline")
        mood_df = pd.DataFrame(mood_events, columns=["Day", "Mood"])
        st.dataframe(mood_df, use_container_width=True, hide_index=True)

    # ── Messages sent/received ────────────────────────────────────────────────
    st.subheader("💬 Communication Activity")
    msgs_sent = [t for t in agent_turns
                 if t["tool"] in ("say_to_agent", "send_message")
                 and t.get("result_status") == "ok"]
    msgs_received = [t for t in turns
                     if t["tool"] in ("say_to_agent", "send_message")
                     and t.get("params", {}).get("target") == agent_name]

    c1, c2, c3 = st.columns(3)
    c1.metric("Messages Sent", len(msgs_sent))
    c2.metric("Messages Received", len(msgs_received))
    crimes_by_agent = load_crimes(world_name)
    my_crimes = [c for c in crimes_by_agent if c.get("actor") == agent_name]
    c3.metric("Crimes Committed", len(my_crimes),
              delta="⚠️ CRIMINAL RECORD" if my_crimes else "✅ Clean")

    if my_crimes:
        st.error(f"**{agent_name} committed {len(my_crimes)} crimes:**")
        for c in my_crimes:
            st.write(f"  • Day {c['day']}: {c['type'].upper()} → {c.get('target', 'location')}")


# ── Page 3: Event Replay ──────────────────────────────────────────────────────

def page_event_replay(worlds):
    st.title("📺 Event Replay — Day-by-Day Story")
    st.caption("Slide through the 15 days and watch the story unfold.")

    if not worlds:
        st.warning("No data found.")
        return

    world_name = st.selectbox("Select World", list(worlds.keys()),
                               format_func=lambda x: WORLD_LABELS.get(x, x))
    awi = worlds[world_name]
    turns = load_turn_log(world_name)
    crimes = load_crimes(world_name)

    max_day = awi[-1]["day"] if awi else 15
    selected_day = st.slider("Select Day", 1, max_day, 1)

    # ── Day summary card ──────────────────────────────────────────────────────
    day_snap = next((s for s in awi if s["day"] == selected_day), awi[-1])
    day_crimes = [c for c in crimes if c["day"] == selected_day]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Agents Alive", day_snap["agents_alive"])
    col2.metric("Crimes Today", len(day_crimes),
                delta="🔴 CRIME DAY" if day_crimes else "✅ Peaceful")
    col3.metric("Cumulative Crimes", day_snap.get("total_crimes", 0))
    col4.metric("Gini", f"{day_snap.get('gini', 0):.3f}")

    # ── Crime events ──────────────────────────────────────────────────────────
    if day_crimes:
        st.subheader(f"🚨 Crimes on Day {selected_day}")
        for c in day_crimes:
            actor_color = AGENT_COLORS.get(c["actor"], "#E74C3C")
            st.markdown(
                f"""<div style="background:#FF000022;border-left:4px solid #FF4444;
                padding:10px;border-radius:6px;margin:6px 0">
                <b style="color:#FF6B6B">{c['type'].upper()}</b> —
                <b style="color:{actor_color}">{c['actor']}</b>
                targeted <b>{c.get('target', 'location')}</b> at {c.get('location','')}
                </div>""",
                unsafe_allow_html=True
            )

    # ── Agent activities ──────────────────────────────────────────────────────
    st.subheader(f"📅 Agent Activities on Day {selected_day}")
    day_turns = [t for t in turns if t["day"] == selected_day]

    # Group by agent
    by_agent: dict = defaultdict(list)
    for t in day_turns:
        by_agent[t["agent"]].append(t)

    cols = st.columns(5)
    agents = list(AGENT_ROLES.keys())
    for i, agent in enumerate(agents):
        col = cols[i % 5]
        agent_day_turns = by_agent.get(agent, [])
        color = AGENT_COLORS.get(agent, "#888888")

        # Summarize activities
        tool_counts: dict = defaultdict(int)
        for t in agent_day_turns:
            tool_counts[t["tool"]] += 1

        top_tools = sorted(tool_counts.items(), key=lambda x: -x[1])[:3]
        tools_str = " · ".join(f"{t[0].replace('_',' ')[:12]}" for t, _ in top_tools)

        crimes_today = [c for c in day_crimes if c["actor"] == agent]
        crime_badge = " 🔴" if crimes_today else ""

        col.markdown(
            f"""<div style="background:{color}22;border:1px solid {color}55;
            padding:8px;border-radius:6px;margin:2px">
            <b style="color:{color};font-size:13px">{agent}{crime_badge}</b><br>
            <span style="color:#888;font-size:10px">{AGENT_ROLES[agent]}</span><br>
            <span style="color:#aaa;font-size:10px">{len(agent_day_turns)} actions</span><br>
            <span style="color:#777;font-size:9px">{tools_str}</span>
            </div>""",
            unsafe_allow_html=True
        )

    # ── Recent messages ───────────────────────────────────────────────────────
    st.subheader(f"💬 Messages on Day {selected_day}")
    day_messages = [
        t for t in day_turns
        if t["tool"] in ("say_to_agent", "send_message")
        and t.get("result_status") == "ok"
    ][:15]

    if day_messages:
        for msg in day_messages:
            from_color = AGENT_COLORS.get(msg["agent"], "#888")
            to = msg.get("params", {}).get("target", "?")
            to_color = AGENT_COLORS.get(to, "#888")
            content = msg.get("params", {}).get("message", "")[:100]
            st.markdown(
                f"""<div style="padding:6px 0;border-bottom:1px solid #333">
                <b style="color:{from_color}">{msg['agent']}</b>
                <span style="color:#666"> → </span>
                <b style="color:{to_color}">{to}</b>:
                <span style="color:#ccc"> "{content}"</span>
                </div>""",
                unsafe_allow_html=True
            )
    else:
        st.caption("No messages on this day.")

    # ── AWI progress bar ──────────────────────────────────────────────────────
    st.subheader("📈 Progress Through the Simulation")
    progress_data = [{"Day": s["day"], "Crimes": s.get("total_crimes", 0),
                      "Gini": s.get("gini", 0),
                      "Alive": s["agents_alive"]} for s in awi if s["day"] <= selected_day]
    if progress_data:
        prog_df = pd.DataFrame(progress_data)
        col_a, col_b = st.columns(2)
        with col_a:
            fig_p = px.line(prog_df, x="Day", y="Crimes",
                            title="Cumulative Crimes",
                            color_discrete_sequence=["#E74C3C"])
            fig_p.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                  font_color="#dddddd", height=200)
            st.plotly_chart(fig_p, use_container_width=True)
        with col_b:
            fig_g = px.line(prog_df, x="Day", y="Gini",
                            title="Gini Coefficient Trend",
                            color_discrete_sequence=["#F39C12"])
            fig_g.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                  font_color="#dddddd", height=200)
            st.plotly_chart(fig_g, use_container_width=True)


# ── Page 4: Risk Dashboard ────────────────────────────────────────────────────

def page_risk_dashboard(worlds):
    st.title("🔬 Risk Dashboard — Drift & Threat Analysis")
    st.caption("Scientific metrics: perceptual blindness, tunnel vision, economic drift.")

    if not worlds:
        st.warning("No data found.")
        return

    world_name = st.selectbox("Select World", list(worlds.keys()),
                               format_func=lambda x: WORLD_LABELS.get(x, x))
    awi = worlds[world_name]
    sensorium = load_sensorium(world_name)
    threats = load_threats(world_name)

    # ── Sensorium ─────────────────────────────────────────────────────────────
    st.subheader("👁️ Sensorium Analysis — Perceptual Blindness")
    if sensorium:
        world_ratio = sensorium.get("world_sensing_pct", "?")
        benchmark = sensorium.get("civ6_benchmark", "1-2%")
        col1, col2, col3 = st.columns(3)
        col1.metric("World Sensing Ratio", world_ratio,
                    delta=f"vs Civ VI: {benchmark}", delta_color="normal")
        col2.metric("Total Actions", sensorium.get("total_actions", 0))
        col3.metric("Sensing Calls", sensorium.get("total_sensing", 0))

        daily = sensorium.get("daily_trend", {})
        if daily:
            days_sorted = sorted(int(k) for k in daily.keys())
            df_sens = pd.DataFrame({
                "Day": days_sorted,
                "Sensing %": [daily[str(d)] * 100 for d in days_sorted],
            })
            fig_sens = px.area(df_sens, x="Day", y="Sensing %",
                               title="Sensing Ratio Over Time (declining = drift)",
                               color_discrete_sequence=["#4285F4"])
            fig_sens.add_hline(y=1.5, line_dash="dot", line_color="#FF6B6B",
                                annotation_text="Civ VI baseline (1-2%)")
            fig_sens.update_layout(plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                    font_color="#dddddd", height=300)
            st.plotly_chart(fig_sens, use_container_width=True)

        agent_ratios = sensorium.get("agent_ratios", {})
        if agent_ratios:
            ar_df = pd.DataFrame([
                {"Agent": ag, "Sensing %": round(v["sensing_ratio"] * 100, 1)}
                for ag, v in agent_ratios.items()
            ]).sort_values("Sensing %")
            fig_ar = px.bar(ar_df, x="Sensing %", y="Agent", orientation="h",
                            title="Per-Agent Sensing Ratio",
                            color="Agent",
                            color_discrete_map={ag: AGENT_COLORS.get(ag, "#888")
                                                for ag in ar_df["Agent"]})
            fig_ar.add_vline(x=2, line_dash="dot", line_color="#FF6B6B",
                              annotation_text="Civ VI baseline")
            fig_ar.update_layout(showlegend=False, height=350,
                                  plot_bgcolor="#1a1d27", paper_bgcolor="#1a1d27",
                                  font_color="#dddddd")
            st.plotly_chart(fig_ar, use_container_width=True)
    else:
        st.info(f"Run `python audit.py --world {world_name} --sensorium` to generate data.")

    st.divider()

    # ── Tunnel Vision ─────────────────────────────────────────────────────────
    st.subheader("🎯 Tunnel Vision Detection")
    if threats and threats.get("tunnel_events"):
        events = threats["tunnel_events"]
        col1, col2 = st.columns(2)
        col1.metric("Tunnel Vision Events", threats["total_tunnel_windows"])
        col2.metric("HIGH Risk Events", threats["high_risk_windows"])

        for ev in events:
            risk_color = "#FF4444" if ev["risk"] == "HIGH" else "#FF9944"
            ignored = ", ".join(ev.get("ignored_agents", [])[:3]) or "none"
            agent_color = AGENT_COLORS.get(ev["agent"], "#fff")
            target_color = AGENT_COLORS.get(ev["dominant_target"], "#fff")
            st.markdown(
                f"""<div style="background:{risk_color}22;border-left:4px solid {risk_color};
                padding:10px;border-radius:6px;margin:6px 0">
                <b style="color:{risk_color}">[{ev['risk']}]</b>
                <b style="color:{agent_color}">{ev['agent']}</b>
                focused <b>{ev['dominant_pct']}</b> on
                <b style="color:{target_color}">{ev['dominant_target']}</b>
                — Days {ev['start_day']}–{ev['end_day']} (HHI={ev['avg_hhi']:.2f})<br>
                <span style="color:#888;font-size:12px">Ignored: {ignored}</span>
                </div>""",
                unsafe_allow_html=True
            )
    elif threats:
        st.success("✅ No tunnel vision detected in this world.")
    else:
        st.info(f"Run `python audit.py --world {world_name} --threats` to analyze.")

    st.divider()

    # ── AWI Metrics ───────────────────────────────────────────────────────────
    st.subheader("📈 AWI Metrics Over 15 Days")
    df_awi = pd.DataFrame(awi)
    if "day" in df_awi.columns:
        df_awi = df_awi.set_index("day")

    tab1, tab2, tab3 = st.tabs(["Population & Safety", "Economy", "Social & Governance"])
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            if "agents_alive" in df_awi:
                st.line_chart(df_awi[["agents_alive"]])
                st.caption("M1 — Population (agents alive)")
        with c2:
            if "total_crimes" in df_awi:
                st.line_chart(df_awi[["total_crimes"]])
                st.caption("M2 — Cumulative Crimes")
    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            if "gini" in df_awi:
                st.line_chart(df_awi[["gini"]])
                st.caption("M8 — Gini (inequality)")
        with c2:
            if "total_credits" in df_awi:
                st.line_chart(df_awi[["total_credits"]])
                st.caption("Total CC in circulation")
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            if "total_proposals" in df_awi:
                st.line_chart(df_awi[["total_proposals"]])
                st.caption("M5 — Governance Proposals")
        with c2:
            if "avg_relationships" in df_awi:
                st.line_chart(df_awi[["avg_relationships"]])
                st.caption("M7 — Avg Relationships/Agent")


# ── Main navigation ───────────────────────────────────────────────────────────

def main():
    worlds = load_worlds()

    st.sidebar.markdown("### 🏝️ AI Freedom Island")
    st.sidebar.markdown("Multi-agent social simulation for AI safety research.")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navigate",
        ["🌍 World Overview", "🧑 Agent Biography", "📺 Event Replay", "🔬 Risk Dashboard"],
        label_visibility="collapsed"
    )

    st.sidebar.divider()
    st.sidebar.markdown(f"**Worlds loaded:** {len(worlds)}")
    for name, awi in worlds.items():
        last = awi[-1]
        color = WORLD_COLORS.get(name, "#888")
        label = WORLD_LABELS.get(name, name)
        crimes = last.get("total_crimes", 0)
        badge = "🔴" if crimes > 5 else ("🟡" if crimes > 0 else "🟢")
        st.sidebar.markdown(
            f"<small><span style='color:{color}'>■</span> {label} {badge}</small>",
            unsafe_allow_html=True
        )

    if page == "🌍 World Overview":
        page_world_overview(worlds)
    elif page == "🧑 Agent Biography":
        page_agent_biography(worlds)
    elif page == "📺 Event Replay":
        page_event_replay(worlds)
    elif page == "🔬 Risk Dashboard":
        page_risk_dashboard(worlds)


if __name__ == "__main__":
    main()
