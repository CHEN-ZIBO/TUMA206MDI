"""ALARMS — AI operator assistant + alarm event log"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

import config
from ai_assistant import AIAssistant
from engine import SimulationEngine

BG = "#0d1117"
CARD_BG = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
TEXT_DIM = "#8b949e"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
ORANGE = "#d2991d"
RED = "#f85149"

# ══════════════════════════════════════════════════════════════════════
# GLOBAL CSS — dark industrial theme (matches SCHEMATIC + TRENDS)
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
    .stApp {{ background: {BG}; }}
    header[data-testid="stHeader"] {{
        background: linear-gradient(90deg, {BG}, {CARD_BG}, {BG});
        border-bottom: 1px solid {BORDER};
    }}
    header[data-testid="stHeader"] * {{ color: {TEXT} !important; }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {BG}, #010409);
        border-right: 1px solid {BORDER};
    }}
    [data-testid="stSidebar"] * {{ color: {TEXT_DIM} !important; }}
    [data-testid="stSidebar"] .stButton > button {{
        background: #21262d !important; color: {TEXT} !important;
        border: 1px solid {BORDER} !important; border-radius: 6px !important;
        font-weight: 600 !important; letter-spacing: 0.03em !important;
        text-transform: uppercase !important; font-size: 0.75rem !important;
        transition: all 0.15s !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: #30363d !important; border-color: {ACCENT} !important;
    }}
    [data-testid="stSidebar"] .stButton > button:active {{
        transform: scale(0.97) !important; background: {ACCENT}22 !important;
    }}
    [data-testid="stSidebar"] hr {{ border-color: {BORDER} !important; }}
    .section-label {{
        font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.1em; color: {TEXT_DIM};
        margin: 14px 0 8px 0; padding-bottom: 6px;
        border-bottom: 1px solid {BORDER};
    }}
    .sidebar-section {{
        font-size: 0.55rem; font-weight: 700; text-transform: uppercase;
        letter-spacing: 0.1em; color: {ACCENT}; margin-top: 10px; margin-bottom: 4px;
    }}
    .diagnosis-panel {{
        background: {CARD_BG}; border-radius: 8px;
        border: 1px solid {BORDER}; border-left: 4px solid {ACCENT};
        padding: 14px 18px; margin: 8px 0; color: {TEXT};
    }}
    .confidence-high {{
        background: {GREEN}33; color: {GREEN}; padding: 2px 10px;
        border-radius: 10px; font-size: 0.7rem; font-weight: 700;
    }}
    .confidence-medium {{
        background: {ORANGE}33; color: {ORANGE}; padding: 2px 10px;
        border-radius: 10px; font-size: 0.7rem; font-weight: 700;
    }}
    .confidence-model {{
        background: {ACCENT}33; color: {ACCENT}; padding: 2px 10px;
        border-radius: 10px; font-size: 0.7rem; font-weight: 700;
    }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# ENGINE + AI
# ══════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_engine() -> SimulationEngine:
    e = SimulationEngine(use_mqtt=os.environ.get("USE_MQTT", "0") == "1")
    e.start()
    return e

@st.cache_resource
def get_assistant() -> AIAssistant:
    return AIAssistant()

engine = get_engine()
assistant = get_assistant()

if "refresh_s" not in st.session_state:
    st.session_state["refresh_s"] = 3
if "window_s" not in st.session_state:
    st.session_state["window_s"] = config.HISTORY_WINDOW_S

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:8px 0;">
        <div style="font-size:1rem;font-weight:700;color:{TEXT};letter-spacing:0.06em;">ALARMS</div>
        <div style="font-size:0.52rem;color:{ACCENT};letter-spacing:0.1em;">AI DIAGNOSTICS</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    # ── AI API key configuration ──────────────────────────────────────
    st.markdown('<div class="sidebar-section">AI Configuration</div>', unsafe_allow_html=True)
    saved_key = st.session_state.get("ai_api_key", assistant.api_key)
    new_key = st.text_input(
        "Anthropic API Key",
        value=saved_key,
        type="password",
        placeholder="sk-ant-...",
        label_visibility="collapsed",
        help="Enter your Anthropic API key to enable Claude-powered diagnosis.",
    )
    if new_key != saved_key:
        st.session_state["ai_api_key"] = new_key
        assistant.update_api_key(new_key)
        st.session_state.pop("ai_cache", None)  # clear stale cache on key change
    mode_label = f"Claude ({config.ANTHROPIC_MODEL})" if assistant.using_claude else "Rule-based (offline)"
    st.caption(f"Engine: {mode_label}")

    st.divider()
    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
    if st.button("Force Analysis", use_container_width=True):
        st.session_state.pop("ai_cache", None)
        st.rerun()
    if st.button("Clear Cache", use_container_width=True):
        st.session_state.pop("ai_cache", None)
        st.success("Cache cleared.")

# ══════════════════════════════════════════════════════════════════════
# MAIN — ALARMS PAGE
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:linear-gradient(90deg,{BG},{CARD_BG},{BG});border-radius:8px;
padding:10px 22px;margin-bottom:6px;border-bottom:1px solid {BORDER};">
<div style="font-size:1.1rem;font-weight:700;color:{TEXT};letter-spacing:0.06em;">ALARMS</div>
<div style="font-size:0.58rem;color:{TEXT_DIM};letter-spacing:0.05em;">FAULT DIAGNOSIS &bull; OPERATOR RECOMMENDATIONS &bull; EVENT HISTORY</div>
</div>""", unsafe_allow_html=True)


@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def alarms_view():
    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", config.ALARM_NONE))
    history = engine.historian.recent(window_s=st.session_state["window_s"])

    # ── Current Status ──
    col1, col2, col3 = st.columns(3)
    plc_state = latest.get("plc_state", "IDLE")
    alarm_label = config.ALARM_LABELS.get(alarm_code, "None")
    fault_label = config.FAULT_LABELS.get(int(latest.get("fault_status", 0)), "Normal")

    col1.metric("PLC State", plc_state)
    col2.metric("Active Alarm", alarm_label, delta="ACTIVE" if alarm_code else "CLEAR")
    col3.metric("Fault Status", fault_label)

    st.divider()

    # ── AI Diagnosis Panel ──
    st.markdown('<div class="section-label">Diagnosis & Recommendation</div>', unsafe_allow_html=True)

    cache = st.session_state.setdefault("ai_cache", {})

    if alarm_code:
        sensor_fp = f"{latest.get('pasteur_temp',0):.0f}_{latest.get('tank_level',0):.0f}_{latest.get('flow_rate',0):.0f}"
        cache_key = f"{alarm_code}_{sensor_fp}"
        if cache_key not in cache:
            with st.spinner("Analyzing system state..."):
                cache[cache_key] = assistant.diagnose(latest, alarm_code, history)
        result = cache.get(cache_key)

        if result:
            conf = result.get("confidence_level", "unknown")
            conf_class = {"high": "confidence-high", "medium": "confidence-medium"}.get(conf, "confidence-model")
            st.markdown(f"""
            <div class="diagnosis-panel">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    <span style="font-size:1rem;font-weight:700;color:{TEXT};">{result['diagnosis_label']}</span>
                    <span class="{conf_class}">{conf.upper()}</span>
                    <span style="font-size:0.65rem;color:{TEXT_DIM};">via {result.get('engine', 'unknown')}</span>
                </div>
                <div style="color:{TEXT};line-height:1.65;font-size:0.88rem;padding:6px 0;">
                    {result['recommendation_text']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{TEXT_DIM};font-size:0.85rem;padding:12px 0;">No active alarms — system operating normally. The AI assistant activates automatically when an alarm is detected.</div>', unsafe_allow_html=True)

    st.divider()

    # ── Alarm Event Log ──
    st.markdown('<div class="section-label">Alarm Event Log</div>', unsafe_allow_html=True)

    alarms = engine.historian.recent_alarms(100)
    if alarms:
        adf = pd.DataFrame(alarms)
        adf["time"] = pd.to_datetime(adf["ts"], unit="s")
        adf = adf.sort_values("time", ascending=False)

        total_alarms = len(adf)
        unique_types = adf["label"].nunique() if "label" in adf.columns else 0
        st.caption(f"{total_alarms} events recorded · {unique_types} alarm types")

        display_cols = [c for c in ["time", "label", "description"] if c in adf.columns]
        if display_cols:
            st.dataframe(adf[display_cols], use_container_width=True, hide_index=True, height=300)

        if "label" in adf.columns and total_alarms > 1:
            st.markdown('<div class="section-label" style="margin-top:12px;">Alarm Type Distribution</div>', unsafe_allow_html=True)
            dist = adf["label"].value_counts()
            cols = st.columns(min(len(dist), 6))
            for i, (label, count) in enumerate(dist.items()):
                cols[i % len(cols)].metric(label, count)
    else:
        st.info("No alarm events recorded yet. Start the line and inject faults to see alarms here.")


alarms_view()
