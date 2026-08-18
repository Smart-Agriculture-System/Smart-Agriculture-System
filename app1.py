from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import joblib
import os
import requests
import pandas as pd

app = FastAPI(title="Smart Irrigation API", version="2.0")

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "irrigation_model.pkl")

CHANNEL_ID = "CHANNEL_ID"
READ_API_KEY = "READ_API_KEY"
WRITE_API_KEY = "WRITE_API_KEY"

THINGSPEAK_READ_URL = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds/last.json?api_key={READ_API_KEY}"
THINGSPEAK_WRITE_URL = "https://api.thingspeak.com/update"

# =========================================================
# LOAD MODEL
# =========================================================
model = None

try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")
except Exception as e:
    print("Error loading model:", e)
    model = None

# =========================================================
# REQUEST SCHEMAS
# =========================================================
class InputData(BaseModel):
    features: List[float] = Field(..., min_length=11, max_length=11)

class PumpCommand(BaseModel):
    pump: int = Field(..., ge=0, le=1)

# =========================================================
# HELPERS
# =========================================================
FEATURE_COLUMNS = [
    "ACHP", "PHR", "ALAP", "ANPL",
    "ARD", "ADWR", "PDMVG", "ARL",
    "AWWR", "ADWV", "PDMRG"
]

def safe_float(val, default=0.0):
    try:
        if val is None or val == "":
            return default
        return float(val)
    except Exception:
        return default

def calculate_duration(soil):
    """
    Soil sensor assumption:
    higher raw value = drier soil
    Adjust thresholds after calibration if needed.
    """
    if soil > 700:
        return 15
    elif soil > 500:
        return 10
    else:
        return 0

def calculate_water(duration):
    return round(duration * 0.1, 2)

def next_irrigation(temp):
    if temp > 35:
        return 2
    elif temp > 25:
        return 4
    else:
        return 6

def get_sensor_data_from_thingspeak():
    """
    Arduino sends:
    field1 = temperature
    field2 = humidity
    field3 = soil moisture
    field4 = rain
    field5 = light
    """
    response = requests.get(THINGSPEAK_READ_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    sensor_data = {
        "temperature": safe_float(data.get("field1")),
        "humidity": safe_float(data.get("field2")),
        "soil": safe_float(data.get("field3")),
        "rain": safe_float(data.get("field4")),
        "light": safe_float(data.get("field5")),
        "created_at": data.get("created_at"),
        "entry_id": data.get("entry_id"),
    }

    return sensor_data

def build_feature_vector(sensor_data):
    """
    Must match model training order exactly.
    Since live hardware provides fewer variables than training data,
    some values remain fixed dummy values.
    """
    features = [
        sensor_data["temperature"],  # ACHP
        sensor_data["humidity"],     # PHR
        sensor_data["light"],        # ALAP
        sensor_data["rain"],         # ANPL
        10,                          # ARD
        5,                           # ADWR
        7,                           # PDMVG
        2,                           # ARL
        8,                           # AWWR
        4,                           # ADWV
        6                            # PDMRG
    ]
    return features

def predict_from_features(features):
    if model is None:
        raise ValueError("Model not loaded.")

    if len(features) != 11:
        raise ValueError("Exactly 11 features are required.")

    input_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
    prediction = model.predict(input_df)[0]
    return int(prediction)

def apply_safety_rules(predicted_pump, sensor_data):
    """
    Safe practical control:
    - rain detected => OFF
    - very dry soil => ON
    - wet soil => OFF

    Adjust thresholds for your sensor after testing.
    """
    soil = sensor_data["soil"]
    rain = sensor_data["rain"]

    pump = predicted_pump

    # Rain detected -> stop pump
    if rain == 1:
        pump = 0

    # Soil calibration rules
    elif soil > 700:
        pump = 1
    elif soil < 400:
        pump = 0

    return pump

def send_decision_to_thingspeak(pump):
    params = {
        "api_key": WRITE_API_KEY,
        "field6": int(pump)
    }

    response = requests.get(THINGSPEAK_WRITE_URL, params=params, timeout=10)
    response.raise_for_status()

    body = str(response.text).strip()
    if body == "0":
        raise ValueError("ThingSpeak rejected the update.")

    return body

def build_result(sensor_data, features, pump):
    soil = sensor_data["soil"]
    temp = sensor_data["temperature"]

    duration = calculate_duration(soil) if pump == 1 else 0
    water = calculate_water(duration) if pump == 1 else 0.0
    next_time = next_irrigation(temp)

    return {
        "sensor_data": sensor_data,
        "features_used": features,
        "irrigate": "YES" if pump == 1 else "NO",
        "pump": pump,
        "duration": duration,
        "water_used": water,
        "next_irrigation": next_time
    }

# =========================================================
# API ENDPOINTS
# =========================================================
@app.get("/")
def root():
    return {
        "message": "Smart Irrigation API is running",
        "model_loaded": model is not None,
        "channel_id": CHANNEL_ID
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None
    }

@app.get("/sensor/latest")
def sensor_latest():
    try:
        sensor_data = get_sensor_data_from_thingspeak()
        return {
            "success": True,
            "sensor_data": sensor_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/predict")
def predict(data: InputData):
    """
    Manual feature prediction.
    Send exactly 11 features in trained order:
    [ACHP, PHR, ALAP, ANPL, ARD, ADWR, PDMVG, ARL, AWWR, ADWV, PDMRG]
    """
    try:
        if model is None:
            return {"success": False, "error": "Model not loaded."}

        features = data.features
        raw_prediction = predict_from_features(features)
        pump = 1 if raw_prediction == 1 else 0

        # Here we do not have full live sensor context, so no soil/rain safety override.
        # We still return result structure.
        result = {
            "success": True,
            "features_used": features,
            "irrigate": "YES" if pump == 1 else "NO",
            "pump": pump,
            "duration": 10 if pump == 1 else 0,
            "water_used": calculate_water(10) if pump == 1 else 0.0,
            "next_irrigation": 4
        }

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/predict_live")
def predict_live(write_to_thingspeak: bool = True):
    """
    1. Read latest ThingSpeak sensor data
    2. Build feature vector
    3. Predict using model
    4. Apply safety rules
    5. Optionally write pump command to field6
    """
    try:
        if model is None:
            return {"success": False, "error": "Model not loaded."}

        sensor_data = get_sensor_data_from_thingspeak()
        features = build_feature_vector(sensor_data)

        raw_prediction = predict_from_features(features)
        predicted_pump = 1 if raw_prediction == 1 else 0

        final_pump = apply_safety_rules(predicted_pump, sensor_data)

        result = build_result(sensor_data, features, final_pump)
        result["raw_model_prediction"] = predicted_pump

        if write_to_thingspeak:
            entry_id = send_decision_to_thingspeak(final_pump)
            result["thingspeak_write_entry"] = entry_id

        return {
            "success": True,
            **result
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/pump/write")
def pump_write(command: PumpCommand):
    """
    Manual pump command write to ThingSpeak field6.
    pump = 1 -> ON
    pump = 0 -> OFF
    """
    try:
        entry_id = send_decision_to_thingspeak(command.pump)
        return {
            "success": True,
            "pump": command.pump,
            "thingspeak_write_entry": entry_id,
            "message": "Pump command sent to ThingSpeak field6"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/pump/test/on")
def pump_test_on():
    try:
        entry_id = send_decision_to_thingspeak(1)
        return {
            "success": True,
            "pump": 1,
            "thingspeak_write_entry": entry_id,
            "message": "Pump ON command sent"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/pump/test/off")
def pump_test_off():
    try:
        entry_id = send_decision_to_thingspeak(0)
        return {
            "success": True,
            "pump": 0,
            "thingspeak_write_entry": entry_id,
            "message": "Pump OFF command sent"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}