"""Shared singletons for the dashboard.

All three pages import get_engine() and get_assistant() from HERE so that
@st.cache_resource returns the SAME object across SCHEMATIC / TRENDS / ALARMS.
Each page defining its own get_engine() creates a SEPARATE cached instance
(Streamlit keys the cache by function object identity).
"""
from __future__ import annotations
import os

import streamlit as st

from engine import SimulationEngine
from ai_assistant import AIAssistant


@st.cache_resource
def get_engine() -> SimulationEngine:
    e = SimulationEngine(use_mqtt=os.environ.get("USE_MQTT", "0") == "1")
    e.start()
    return e


@st.cache_resource
def get_assistant() -> AIAssistant:
    return AIAssistant()
