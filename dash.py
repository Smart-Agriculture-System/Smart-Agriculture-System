import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="Smart Irrigation Dashboard", layout="wide")

# =========================================================
# CONFIG
# =========================================================
API_BASE_URL = "API_BASE_URL"
CHANNEL_ID = "CHANNEL_ID"
READ_API_KEY = "READ_API_KEY"

THINGSPEAK_FEEDS_URL = (
    f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
    f"?api_key={READ_API_KEY}&results=50"
)

# =========================================================
# LANGUAGE DICTIONARY
# =========================================================
LANG = {
    "en": {
        "title": "Smart Irrigation System",
        "temperature": "Temperature",
        "humidity": "Humidity",
        "soil_moisture": "Soil Moisture",
        "light": "Light",
        "rain": "Rain",
        "dashboard": "Dashboard",
        "analytics": "Analytics",
        "logs": "Logs",
        "irrigation_required": "Irrigation Required 🚨",
        "no_irrigation": "No Irrigation Needed ✅",
        "api_not_running": "FastAPI server not reachable",
        "thingspeak_error": "ThingSpeak connection failed",
        "prediction": "Prediction",
        "pump_status": "Pump Status",
        "duration": "Duration",
        "water_used": "Water Used",
        "next_irrigation": "Next Irrigation",
        "soil_dry": "Soil is DRY",
        "soil_optimal": "Soil is OPTIMAL",
        "soil_wet": "Soil is WET",
        "sensor_trends": "Sensor Trends",
        "summary": "Summary",
        "avg_soil": "Average Soil Moisture",
        "max_temp": "Max Temperature",
        "min_humidity": "Min Humidity",
        "latest_update": "Latest Update",
        "refresh_data": "Refresh Dashboard",
        "run_prediction": "Run Auto Prediction",
        "total_logs": "Total Logs",
        "total_duration": "Total Duration",
        "total_water": "Total Water Used",
        "select_language": "Select Language / भाषा चुनें",
        "live_data": "Live Data",
        "api_success": "API connected successfully",
        "pump_on": "Pump ON",
        "pump_off": "Pump OFF",
        "status_section": "System Status"
    },
    "hi": {
        "title": "स्मार्ट सिंचाई प्रणाली",
        "temperature": "तापमान",
        "humidity": "आर्द्रता",
        "soil_moisture": "मिट्टी की नमी",
        "light": "प्रकाश",
        "rain": "वर्षा",
        "dashboard": "डैशबोर्ड",
        "analytics": "विश्लेषण",
        "logs": "लॉग्स",
        "irrigation_required": "सिंचाई आवश्यक 🚨",
        "no_irrigation": "सिंचाई की आवश्यकता नहीं ✅",
        "api_not_running": "FastAPI सर्वर उपलब्ध नहीं है",
        "thingspeak_error": "ThingSpeak कनेक्शन विफल",
        "prediction": "पूर्वानुमान",
        "pump_status": "पंप स्थिति",
        "duration": "अवधि",
        "water_used": "पानी का उपयोग",
        "next_irrigation": "अगली सिंचाई",
        "soil_dry": "मिट्टी सूखी है",
        "soil_optimal": "मिट्टी उचित है",
        "soil_wet": "मिट्टी गीली है",
        "sensor_trends": "सेंसर रुझान",
        "summary": "सारांश",
        "avg_soil": "औसत मिट्टी की नमी",
        "max_temp": "अधिकतम तापमान",
        "min_humidity": "न्यूनतम आर्द्रता",
        "latest_update": "अंतिम अपडेट",
        "refresh_data": "डैशबोर्ड रीफ्रेश करें",
        "run_prediction": "ऑटो प्रेडिक्शन चलाएँ",
        "total_logs": "कुल लॉग्स",
        "total_duration": "कुल अवधि",
        "total_water": "कुल पानी उपयोग",
        "select_language": "भाषा चुनें / Select Language",
        "live_data": "लाइव डेटा",
        "api_success": "API सफलतापूर्वक कनेक्ट हुआ",
        "pump_on": "पंप चालू",
        "pump_off": "पंप बंद",
        "status_section": "सिस्टम स्थिति"
    }
}

# =========================================================
# LANGUAGE SELECTOR
# =========================================================
lang = st.selectbox(LANG["en"]["select_language"], ["English", "हिन्दी"])
lang_code = "en" if lang == "English" else "hi"

st.title("🌱 " + LANG[lang_code]["title"])

# =========================================================
# SESSION STATE
# =========================================================
if "irrigation_logs" not in st.session_state:
    st.session_state.irrigation_logs = []

# =========================================================
# HELPERS
# =========================================================
def safe_float(val, default=0.0):
    try:
        if val is None or val == "":
            return default
        return float(val)
    except Exception:
        return default

@st.cache_data(ttl=30)
def fetch_thingspeak_history():
    try:
        res = requests.get(THINGSPEAK_FEEDS_URL, timeout=10)
        res.raise_for_status()
        data = res.json()
        feeds = data.get("feeds", [])

        if not feeds:
            return pd.DataFrame()

        df = pd.DataFrame(feeds)
        df["time"] = pd.to_datetime(df["created_at"], errors="coerce")
        df["temperature"] = df["field1"].apply(safe_float)
        df["humidity"] = df["field2"].apply(safe_float)
        df["soil_moisture"] = df["field3"].apply(safe_float)
        df["rain"] = df["field4"].apply(safe_float)
        df["light"] = df["field5"].apply(safe_float)
        df = df.dropna(subset=["time"])

        return df
    except Exception:
        return pd.DataFrame()

def call_api(endpoint):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return res.json(), None
    except Exception as e:
        return None, str(e)

def get_latest_sensor_data():
    response, error = call_api("/sensor/latest")
    if error or not response:
        return None, error

    if response.get("success"):
        return response.get("sensor_data", {}), None

    return None, response.get("error", "Unknown error")

def run_live_prediction(write=False):
    endpoint = "/predict_live?write_to_thingspeak=true" if write else "/predict_live?write_to_thingspeak=false"
    response, error = call_api(endpoint)

    if error or not response:
        return None, error

    if response.get("success"):
        return response, None

    return None, response.get("error", "Unknown error")

def add_log(result):
    log_entry = {
        "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Temperature": result["sensor_data"].get("temperature", 0),
        "Humidity": result["sensor_data"].get("humidity", 0),
        "Soil": result["sensor_data"].get("soil", 0),
        "Rain": result["sensor_data"].get("rain", 0),
        "Light": result["sensor_data"].get("light", 0),
        "Pump": "ON" if result.get("pump", 0) == 1 else "OFF",
        "Decision": result.get("irrigate", "NO"),
        "Duration (sec)": result.get("duration", 0),
        "Water Used (liters)": result.get("water_used", 0.0),
        "Next Irrigation (hrs)": result.get("next_irrigation", 0)
    }
    st.session_state.irrigation_logs.append(log_entry)
    st.session_state.irrigation_logs = st.session_state.irrigation_logs[-30:]

# =========================================================
# TOP BUTTONS
# =========================================================
b1, b2 = st.columns(2)

with b1:
    if st.button("🔄 " + LANG[lang_code]["refresh_data"], use_container_width=True):
        st.cache_data.clear()
        st.rerun()

with b2:
    if st.button("🤖 " + LANG[lang_code]["run_prediction"], use_container_width=True):
        result, error = run_live_prediction(write=True)
        if error:
            st.error(f"{LANG[lang_code]['api_not_running']}: {error}")
        else:
            add_log(result)
            st.success("Prediction run successfully and pump updated automatically.")
            st.rerun()

# =========================================================
# LOAD DATA
# =========================================================
sensor_data, sensor_error = get_latest_sensor_data()

if sensor_error:
    st.warning(f"{LANG[lang_code]['api_not_running']}: {sensor_error}")
    latest_sensor = {
        "temperature": 0.0,
        "humidity": 0.0,
        "soil": 0.0,
        "rain": 0.0,
        "light": 0.0,
        "created_at": str(datetime.now()),
        "entry_id": "-"
    }
else:
    latest_sensor = sensor_data
    st.success(LANG[lang_code]["api_success"])

history_df = fetch_thingspeak_history()

prediction_result, prediction_error = run_live_prediction(write=False)

if prediction_error or not prediction_result:
    prediction_result = {
        "sensor_data": latest_sensor,
        "irrigate": "NO",
        "pump": 0,
        "duration": 0,
        "water_used": 0.0,
        "next_irrigation": 0
    }

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3 = st.tabs([
    "📊 " + LANG[lang_code]["dashboard"],
    "📈 " + LANG[lang_code]["analytics"],
    "📜 " + LANG[lang_code]["logs"]
])

# =========================================================
# DASHBOARD TAB
# =========================================================
with tab1:
    st.subheader(LANG[lang_code]["live_data"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🌡 " + LANG[lang_code]["temperature"], f"{safe_float(latest_sensor.get('temperature')):.1f} °C")
    c2.metric("💧 " + LANG[lang_code]["humidity"], f"{safe_float(latest_sensor.get('humidity')):.1f} %")
    c3.metric("🌱 " + LANG[lang_code]["soil_moisture"], f"{safe_float(latest_sensor.get('soil')):.1f}")
    c4.metric("🌧 " + LANG[lang_code]["rain"], f"{safe_float(latest_sensor.get('rain')):.1f}")
    c5.metric("☀ " + LANG[lang_code]["light"], f"{safe_float(latest_sensor.get('light')):.1f}")

    st.markdown("---")

    i1, i2, i3 = st.columns(3)
    i1.write(f"**{LANG[lang_code]['latest_update']}:** {latest_sensor.get('created_at', '-')}")
    i2.write(f"**Entry ID:** {latest_sensor.get('entry_id', '-')}")
    i3.write(f"**{LANG[lang_code]['prediction']}:** {prediction_result.get('irrigate', 'NO')}")

    st.markdown("---")

    if prediction_result.get("irrigate") == "YES":
        st.error(LANG[lang_code]["irrigation_required"])
    else:
        st.success(LANG[lang_code]["no_irrigation"])

    soil_value = safe_float(latest_sensor.get("soil"))

    if soil_value > 700:
        st.warning(LANG[lang_code]["soil_dry"])
    elif soil_value > 400:
        st.info(LANG[lang_code]["soil_optimal"])
    else:
        st.success(LANG[lang_code]["soil_wet"])

    st.markdown("---")

    p1, p2, p3, p4 = st.columns(4)
    p1.metric(
        LANG[lang_code]["pump_status"],
        LANG[lang_code]["pump_on"] if prediction_result.get("pump") == 1 else LANG[lang_code]["pump_off"]
    )
    p2.metric("⏱ " + LANG[lang_code]["duration"], f"{prediction_result.get('duration', 0)} sec")
    p3.metric("💧 " + LANG[lang_code]["water_used"], f"{prediction_result.get('water_used', 0.0):.2f} L")
    p4.metric("⏳ " + LANG[lang_code]["next_irrigation"], f"{prediction_result.get('next_irrigation', 0)} hrs")

# =========================================================
# ANALYTICS TAB
# =========================================================
with tab2:
    st.subheader(LANG[lang_code]["sensor_trends"])

    if not history_df.empty and len(history_df) > 1:
        chart_df = history_df.set_index("time")

        st.line_chart(chart_df[["soil_moisture"]])
        st.line_chart(chart_df[["temperature"]])
        st.line_chart(chart_df[["humidity"]])
        st.line_chart(chart_df[["light"]])

        st.markdown("---")
        st.subheader(LANG[lang_code]["summary"])

        a1, a2, a3 = st.columns(3)
        a1.metric(LANG[lang_code]["avg_soil"], f"{chart_df['soil_moisture'].mean():.2f}")
        a2.metric(LANG[lang_code]["max_temp"], f"{chart_df['temperature'].max():.2f} °C")
        a3.metric(LANG[lang_code]["min_humidity"], f"{chart_df['humidity'].min():.2f} %")
    else:
        st.info(LANG[lang_code]["thingspeak_error"])

# =========================================================
# LOGS TAB
# =========================================================
with tab3:
    log_df = pd.DataFrame(st.session_state.irrigation_logs)

    if not log_df.empty:
        st.dataframe(log_df, use_container_width=True)

        total_logs = len(log_df)
        total_duration = log_df["Duration (sec)"].sum()
        total_water = log_df["Water Used (liters)"].sum()

        l1, l2, l3 = st.columns(3)
        l1.metric(LANG[lang_code]["total_logs"], total_logs)
        l2.metric(LANG[lang_code]["total_duration"], f"{total_duration} sec")
        l3.metric(LANG[lang_code]["total_water"], f"{total_water:.2f} L")
    else:
        st.info("No logs available yet.")