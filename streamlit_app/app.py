import os
import json
import requests
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from dictionary_utils import excel_to_json


# ------------------------------------------------------------------------------
# Streamlit Config
# ------------------------------------------------------------------------------
st.set_page_config(page_title="AC MQTT Live Parser", layout="wide")

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
st.write("Backend URL =", BACKEND_BASE_URL)

st.title("📡 AC Dictionary → JSON → Live MQTT Parser")


# ------------------------------------------------------------------------------
# session_state initialization
# ------------------------------------------------------------------------------
DEFAULTS = {
    "device_id": "EZMCSACD00001",
    "topic": "/AC/2/EZMCSACD00001/Datalog",
    "broker": "ecozen.ai",
    "port": 1883,
    "registers": None,
    "latest_data": None,
    "history": []   # <-- parsed message history
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ------------------------------------------------------------------------------
# INPUTS
# ------------------------------------------------------------------------------
st.subheader("Dictionary & MQTT Configuration")

col_a, col_b = st.columns(2)

with col_a:
    st.session_state.device_id = st.text_input(
        "Device ID",
        value=st.session_state.device_id
    )

    st.session_state.topic = st.text_input(
        "MQTT Subscriber Topic",
        value=f"/AC/2/{st.session_state.device_id}/Datalog",
    )

with col_b:
    st.session_state.broker = st.text_input(
        "MQTT Broker",
        value=st.session_state.broker
    )
    st.session_state.port = st.number_input(
        "MQTT Port",
        value=st.session_state.port,
        step=1
    )

uploaded_excel = st.file_uploader("Upload Dictionary Excel", type=["xlsx"])


# ------------------------------------------------------------------------------
# Excel → JSON conversion
# ------------------------------------------------------------------------------
if uploaded_excel and st.button("Convert Excel → JSON"):
    try:
        registers = excel_to_json(uploaded_excel)
        st.session_state.registers = registers

        st.success("✅ Dictionary JSON generated from Excel")
        st.json(registers[:5])

        st.download_button(
            "Download dictionary.json",
            json.dumps(registers, indent=2),
            "dictionary.json",
            "application/json",
        )
    except Exception as e:
        st.error(f"Error during conversion: {e}")

st.markdown("---")


# ------------------------------------------------------------------------------
# Configure Backend
# ------------------------------------------------------------------------------
st.header("Configure Backend MQTT Listener")

if st.button("🚀 Send Configuration to Backend"):
    if not st.session_state.registers:
        st.error("Please convert an Excel dictionary first!")
    else:
        payload = {
            "device_id": st.session_state.device_id,
            "topic": st.session_state.topic,
            "registers": st.session_state.registers,
            "broker": st.session_state.broker,
            "port": int(st.session_state.port),
        }
        try:
            resp = requests.post(
                f"{BACKEND_BASE_URL}/configure",
                json=payload,
                timeout=10
            )
            if resp.status_code == 200:
                st.success(f"Backend configured: {resp.json()}")
            else:
                st.error(f"Backend error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

st.markdown("---")


# ------------------------------------------------------------------------------
# LIVE DATA VIEWER (Auto-refresh every 5s)
# ------------------------------------------------------------------------------
st.header("Live Data Viewer")

auto_refresh = st.checkbox("🔄 Auto-refresh every 5 seconds")

# Only refresh this section, not entire script
if auto_refresh:
    st.autorefresh(interval=5000, key="mqtt_autorefresh")

col1, col2 = st.columns([1, 2])


with col1:
    if st.button("Manual Refresh Latest Message"):
        try:
            resp = requests.get(f"{BACKEND_BASE_URL}/latest", timeout=5)
            if resp.status_code == 200:
                st.session_state.latest_data = resp.json()
            else:
                st.error(f"Backend error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")


# If auto-refresh is ON, fetch latest automatically
if auto_refresh:
    try:
        resp = requests.get(f"{BACKEND_BASE_URL}/latest", timeout=5)
        if resp.status_code == 200:
            st.session_state.latest_data = resp.json()
        else:
            st.error(f"Backend error {resp.status_code}: {resp.text}")
    except Exception as e:
        st.error(f"Could not reach backend: {e}")


with col2:
    latest = st.session_state.latest_data

    if latest:
        st.subheader("📦 Latest Raw Packet")
        st.code(latest.get("raw") or "No data yet")

        parsed_rows = latest.get("parsed")

        if parsed_rows:
            df = pd.DataFrame(parsed_rows)
            st.subheader("🧩 Latest Parsed Message")
            st.dataframe(df)

            # Add to history if new
            if not st.session_state.history or st.session_state.history[-1] != parsed_rows:
                st.session_state.history.append(parsed_rows)

        else:
            st.info("No parsed data yet – waiting for MQTT messages.")

    else:
        st.info("Click 'Manual Refresh Latest Message' to fetch current data.")


# ------------------------------------------------------------------------------
# SHOW HISTORY
# ------------------------------------------------------------------------------
st.markdown("---")
st.subheader("📜 History of Parsed Messages (auto-growing)")

if st.session_state.history:
    for i, msg in enumerate(reversed(st.session_state.history[-20:])):  # last 20 msgs
        st.write(f"### Message #{len(st.session_state.history)-i}")
        st.dataframe(pd.DataFrame(msg))
else:
    st.info("No history available yet.")
