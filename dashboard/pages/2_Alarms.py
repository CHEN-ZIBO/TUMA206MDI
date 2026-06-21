"""ALARMS — AI operator assistant + alarm event log"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st

import config
from shared import get_engine, get_assistant

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
# CSS — dark industrial theme (matches SCHEMATIC + TRENDS)
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
        padding: 14px 18px; margin: 8px 0;
    }}
    .chat-user {{
        background: #1c2128; border: 1px solid {BORDER}; border-radius: 8px;
        padding: 10px 14px; margin: 6px 0; color: {TEXT}; font-size: 0.88rem;
    }}
    .chat-ai {{
        background: {CARD_BG}; border: 1px solid {BORDER}; border-left: 3px solid {ACCENT};
        border-radius: 8px; padding: 10px 14px; margin: 6px 0;
        color: {TEXT}; font-size: 0.88rem; line-height: 1.6;
    }}
    .quick-btn-row {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 10px 0; }}
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
# SHARED SINGLETONS
# ══════════════════════════════════════════════════════════════════════
engine = get_engine()
assistant = get_assistant()

# Session state defaults
for k, v in [("refresh_s", 3), ("window_s", config.HISTORY_WINDOW_S),
             ("chat_history", []), ("pending_question", "")]:
    if k not in st.session_state:
        st.session_state[k] = v

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

    st.markdown('<div class="sidebar-section">AI Configuration</div>', unsafe_allow_html=True)
    saved_key = st.session_state.get("ai_api_key", assistant.api_key)
    new_key = st.text_input(
        "Anthropic API Key", value=saved_key, type="password",
        placeholder="sk-ant-...", label_visibility="collapsed",
        help="Enter your Anthropic API key to enable Claude-powered diagnosis.",
    )
    if new_key != saved_key:
        st.session_state["ai_api_key"] = new_key
        assistant.update_api_key(new_key)
        st.session_state.pop("ai_cache", None)
    mode_label = f"Claude ({config.ANTHROPIC_MODEL})" if assistant.using_claude else "Rule-based (offline)"
    st.caption(f"Engine: {mode_label}")

    st.divider()
    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
    if st.button("Force Diagnosis", use_container_width=True):
        st.session_state.pop("ai_cache", None)
        st.rerun()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state["chat_history"] = []
        st.session_state.pop("ai_cache", None)
        st.rerun()
    st.divider()
    st.session_state["refresh_s"] = st.slider("Refresh (s)", 1, 10, st.session_state["refresh_s"])
    st.session_state["window_s"] = st.slider("History (s)", 30, 600, st.session_state["window_s"], 30)

# ══════════════════════════════════════════════════════════════════════
# PAGE HEADER
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="background:linear-gradient(90deg,{BG},{CARD_BG},{BG});border-radius:8px;
padding:10px 22px;margin-bottom:6px;border-bottom:1px solid {BORDER};">
<div style="font-size:1.1rem;font-weight:700;color:{TEXT};letter-spacing:0.06em;">ALARMS</div>
<div style="font-size:0.58rem;color:{TEXT_DIM};letter-spacing:0.05em;">FAULT DIAGNOSIS &bull; AI CONSULTATION &bull; EVENT HISTORY</div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
# HELPER: run a consult question and add to chat history
# ══════════════════════════════════════════════════════════════════════
def _ask(question: str, latest: dict, history: list) -> None:
    st.session_state["chat_history"].append({"role": "user", "content": question})
    with st.spinner("AI analyzing..."):
        answer = assistant.consult(question, latest, history)
    st.session_state["chat_history"].append({"role": "ai", "content": answer})


# ══════════════════════════════════════════════════════════════════════
# LIVE VIEW (auto-refreshes)
# ══════════════════════════════════════════════════════════════════════
@st.fragment(run_every=f"{st.session_state['refresh_s']}s")
def alarms_view():
    latest = engine.latest()
    alarm_code = int(latest.get("alarm_code", config.ALARM_NONE))
    history = engine.historian.recent(window_s=st.session_state["window_s"])

    # ── Status row ───────────────────────────────────────────────────
    plc_state = latest.get("plc_state", "IDLE")
    alarm_label = config.ALARM_LABELS.get(alarm_code, "None")
    fault_label = config.FAULT_LABELS.get(int(latest.get("fault_status", 0)), "Normal")
    plc_col, alarm_col, fault_col = st.columns(3)
    plc_col.metric("PLC State", plc_state)
    alarm_col.metric("Active Alarm", alarm_label, delta="ACTIVE" if alarm_code else "CLEAR")
    fault_col.metric("Fault Status", fault_label)

    # Inline sensor summary strip
    t = latest.get("pasteur_temp", 0)
    lv = latest.get("tank_level", 0)
    fl = latest.get("flow_rate", 0)
    buf = latest.get("conveyor_queue", 0)
    co = latest.get("cooler_temp", 0)
    t_ok = config.PASTEUR_SAFE_MIN <= float(t) <= config.PASTEUR_SAFE_MAX
    lv_ok = config.TANK_LEVEL_LOW <= float(lv) <= config.TANK_LEVEL_HIGH
    tc = GREEN if t_ok else RED
    lc = GREEN if lv_ok else ORANGE
    st.markdown(
        f'<div style="display:flex;gap:20px;font-size:0.72rem;color:{TEXT_DIM};padding:4px 0 2px 0;">'
        f'<span>Temp <b style="color:{tc}">{t:.1f}°C</b></span>'
        f'<span>Tank <b style="color:{lc}">{lv:.1f}%</b></span>'
        f'<span>Flow <b style="color:{TEXT}">{fl:.1f} L/min</b></span>'
        f'<span>Cooler <b style="color:{TEXT}">{co:.1f}°C</b></span>'
        f'<span>Buffer <b style="color:{TEXT}">{buf} btl</b></span>'
        f'</div>', unsafe_allow_html=True)

    st.divider()

    # ── Auto-Diagnosis (active alarm only) ───────────────────────────
    st.markdown('<div class="section-label">Auto Diagnosis</div>', unsafe_allow_html=True)
    if alarm_code:
        cache = st.session_state.setdefault("ai_cache", {})
        sensor_fp = f"{t:.0f}_{lv:.0f}_{fl:.0f}"
        cache_key = f"{alarm_code}_{sensor_fp}"
        if cache_key not in cache:
            with st.spinner("Analyzing alarm..."):
                cache[cache_key] = assistant.diagnose(latest, alarm_code, history)
        result = cache.get(cache_key, {})
        conf = result.get("confidence_level", "unknown")
        conf_class = {"high": "confidence-high", "medium": "confidence-medium"}.get(conf, "confidence-model")
        st.markdown(f"""
        <div class="diagnosis-panel">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <span style="font-size:0.95rem;font-weight:700;color:{RED};">&#9888; {result.get('diagnosis_label','')}</span>
                <span class="{conf_class}">{conf.upper()}</span>
                <span style="font-size:0.62rem;color:{TEXT_DIM};">via {result.get('engine','')}</span>
            </div>
            <div style="color:{TEXT};line-height:1.65;font-size:0.87rem;">
                {result.get('recommendation_text','')}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="color:{TEXT_DIM};font-size:0.85rem;padding:8px 0 4px 0;">'
            f'No active alarm — line operating normally.</div>', unsafe_allow_html=True)

    st.divider()

    # ── AI Consultation ───────────────────────────────────────────────
    st.markdown('<div class="section-label">AI Consultation</div>', unsafe_allow_html=True)

    # Quick-action buttons — build context-aware prompts from live state
    alarm_ctx = f"Active alarm: {alarm_label}. " if alarm_code else "No active alarm. "
    state_ctx = (f"PLC={plc_state}, Temp={t:.1f}°C, Tank={lv:.1f}%, "
                 f"Flow={fl:.1f}L/min, Cooler={co:.1f}°C, Buffer={buf} bottles.")

    quick_prompts = {
        "Diagnose Alarm": (
            f"{alarm_ctx}Diagnose the root cause and recommend immediate operator actions. {state_ctx}"
        ),
        "Analyze State": (
            f"Analyze the overall process state and identify any risks or abnormalities. {state_ctx}"
        ),
        "Recovery Steps": (
            f"{alarm_ctx}Provide step-by-step recovery procedure to restore normal production. {state_ctx}"
        ),
        "Risk Check": (
            f"Assess potential risks in the next 5 minutes based on current trends. {state_ctx}"
        ),
    }

    qcols = st.columns(len(quick_prompts))
    for col, (label, prompt) in zip(qcols, quick_prompts.items()):
        if col.button(label, use_container_width=True, key=f"qbtn_{label}"):
            _ask(prompt, latest, history)
            st.rerun()

    # Chat history display
    chat = st.session_state.get("chat_history", [])
    if chat:
        chat_html = ""
        for msg in chat:
            if msg["role"] == "user":
                chat_html += f'<div class="chat-user"><b style="color:{ACCENT};">You</b><br>{msg["content"]}</div>'
            else:
                content = msg["content"].replace("\n", "<br>")
                chat_html += f'<div class="chat-ai"><b style="color:{GREEN};">AI</b><br>{content}</div>'
        st.markdown(
            f'<div style="max-height:340px;overflow-y:auto;padding:2px 0;">{chat_html}</div>',
            unsafe_allow_html=True)

    # Free-form input row
    inp_col, btn_col = st.columns([5, 1])
    user_q = inp_col.text_input(
        "Ask the AI", value=st.session_state.get("pending_question", ""),
        placeholder="Ask about current process state, alarms, or recovery steps...",
        label_visibility="collapsed", key="chat_input",
    )
    if btn_col.button("Ask", use_container_width=True, key="chat_send"):
        if user_q.strip():
            _ask(user_q.strip(), latest, history)
            st.session_state["pending_question"] = ""
            st.rerun()

    st.divider()

    # ── Alarm Event Log ───────────────────────────────────────────────
    st.markdown('<div class="section-label">Alarm Event Log</div>', unsafe_allow_html=True)
    alarms = engine.historian.recent_alarms(100)
    if alarms:
        adf = pd.DataFrame(alarms)
        adf["time"] = pd.to_datetime(adf["ts"], unit="s")
        adf = adf.sort_values("time", ascending=False)
        total = len(adf)
        unique = adf["label"].nunique() if "label" in adf.columns else 0
        st.caption(f"{total} events · {unique} types")
        display_cols = [c for c in ["time", "label", "description"] if c in adf.columns]
        if display_cols:
            st.dataframe(adf[display_cols], use_container_width=True, hide_index=True, height=260)
        if "label" in adf.columns and total > 1:
            dist = adf["label"].value_counts()
            dcols = st.columns(min(len(dist), 6))
            for i, (lbl, cnt) in enumerate(dist.items()):
                dcols[i % len(dcols)].metric(lbl, cnt)
    else:
        st.info("No alarm events yet. Start the line and inject faults to see alarms here.")


alarms_view()
