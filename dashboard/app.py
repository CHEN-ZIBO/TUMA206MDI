"""M4 Dashboard — Production Line Control Center"""

from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

st.set_page_config(page_title="Production Line", layout="wide", page_icon="⏣")

# ── Navigation ────────────────────────────────────────────────────────
# Explicit page definitions give full control over sidebar labels.
# Each page file lives alongside this app.py (SCHEMATIC.py) or in pages/.
pg = st.navigation(
    [
        st.Page("SCHEMATIC.py", title="SCHEMATIC", default=True),
        st.Page("pages/1_Trends.py", title="TRENDS"),
        st.Page("pages/2_Alarms.py", title="ALARMS"),
    ],
    position="sidebar",
)
pg.run()
