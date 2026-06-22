"""Cloud Monitoring Dashboard — deploy this on Streamlit Cloud.

Data flow:  local_backend.py  --MQTT-->  HiveMQ Cloud  --MQTT-->  this app
           (your laptop)                (cloud broker)           (Streamlit Cloud)

How to deploy (one-time setup):
  1. Go to https://streamlit.io/cloud → New app
  2. Select your GitHub repo, set Main file path = "cloud_app.py"
  3. In Manage App → Settings → Secrets, add:
       DASHBOARD_MODE = "remote"
       MQTT_HOST = "3c57522d5f2e469d8ced051055a5bf1f.s1.eu.hivemq.cloud"
       MQTT_PORT = "8883"
       MQTT_TLS = "1"
       MQTT_USERNAME = "tumademo"
       MQTT_PASSWORD = "Tuma2026demo"
       MQTT_TOPIC_PREFIX = "tuma206grp1bvg"
  4. Save → Reboot app. Open the URL — live data appears when local_backend.py is running.

Local testing:  DASHBOARD_MODE=remote streamlit run cloud_app.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env for local testing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Load Streamlit Cloud secrets
try:
    import streamlit as st
    for key in ["MQTT_HOST", "MQTT_PORT", "MQTT_TLS", "MQTT_USERNAME",
                "MQTT_PASSWORD", "MQTT_TOPIC_PREFIX",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DASHBOARD_MODE"]:
        try:
            val = st.secrets.get(key)
            if val is not None and key not in os.environ:
                os.environ[key] = str(val)
        except Exception:
            pass
except Exception:
    pass

os.environ.setdefault("DASHBOARD_MODE", "remote")

import dashboard.cloud  # noqa: F401 — self-rendering page
