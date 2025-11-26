import os
import json
import requests
import pandas as pd
import streamlit as st

from dictionary_utils import excel_to_json

# Backend base URL – set this in Streamlit Cloud as an environment variable
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="AC MQTT Live Parser", layout="wide")

st.title("📡 AC Dictionary → JSON → Live MQTT Parser (Frontend)")

# Session state for registers
if "registers" not in st.session_state:
    st.session_state["registers"] = None

# -------------------------------
# INPUTS
# -------------------------------
st.subheader("Dictionary & MQTT Configuration")

col_a, col_b = st.columns(2)

with col_a:
    device_id = st.text_input("Device ID", value="EZMCSACD00001")
    mqtt_topic = st.text_input("MQTT Subscriber Topic", value=f"/AC/2/{device_id}/Datalog")

with col_b:
    broker = st.text_input("MQTT Broker", value="ecozen.ai")
    port = st.number_input("MQTT Port", value=1883, step=1)

uploaded_excel = st.file_uploader("Upload Dictionary Excel", type=["xlsx"])

# Convert Excel → JSON
if uploaded_excel and st.button("Convert Excel → JSON"):
    try:
        registers = excel_to_json(uploaded_excel)
        st.session_state["registers"] = registers

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

st.header("Configure Backend MQTT Listener")

if st.button("🚀 Send Configuration to Backend"):
    if not st.session_state["registers"]:
        st.error("Please convert an Excel dictionary first!")
    else:
        payload = {
            "device_id": device_id,
            "topic": mqtt_topic,
            "registers": st.session_state["registers"],
            "broker": broker,
            "port": int(port),
        }
        try:
            resp = requests.post(f"{BACKEND_BASE_URL}/configure", json=payload, timeout=10)
            if resp.status_code == 200:
                st.success(f"Backend configured: {resp.json()}")
            else:
                st.error(f"Backend error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

st.markdown("---")

st.header("Live Data Viewer")

col1, col2 = st.columns([1, 2])

with col1:
    if st.button("🔄 Manual Refresh Latest Message"):
        try:
            resp = requests.get(f"{BACKEND_BASE_URL}/latest", timeout=5)
            if resp.status_code == 200:
                st.session_state["latest_data"] = resp.json()
            else:
                st.error(f"Backend error {resp.status_code}: {resp.text}")
        except Exception as e:
            st.error(f"Could not reach backend: {e}")

    auto_refresh = st.checkbox("Auto-refresh every 5 seconds", value=False)
    if auto_refresh:
        st.experimental_rerun()  # simple rerun; Streamlit Cloud periodically runs script

with col2:
    latest = st.session_state.get("latest_data", None)

    if latest:
        st.subheader("Latest Raw Packet")
        st.code(latest.get("raw") or "No data yet")

        parsed_rows = latest.get("parsed")
        if parsed_rows:
            df = pd.DataFrame(parsed_rows)
            st.subheader("Latest Parsed DataFrame")
            st.dataframe(df)
        else:
            st.info("No parsed data yet – waiting for MQTT messages.")
    else:
        st.info("Click 'Manual Refresh Latest Message' to fetch current data from backend.")
