#  Smart Agriculture System (IoT + Machine Learning)

##  Overview
An automated irrigation framework combining IoT sensors, cloud infrastructure, and predictive ML models. The system performs real-time environmental monitoring and determines optimal irrigation timing, resulting in significant water conservation.

---

##  Problem Statement
Traditional irrigation methods rely on fixed schedules or manual observation, which often leads to:
- Over-irrigation (water wastage)
- Under-irrigation (low crop yield)

---

##  Solution
This system:
- Collects real-time sensor data  
- Sends it to ThingSpeak cloud  
- Uses a Machine Learning model to predict irrigation  
- Displays results on a Streamlit dashboard  

---

##  System Architecture
Sensors → ESP8266 → ThingSpeak → ML Model → Dashboard → Irrigation Decision

---

##  Features
- Real-time monitoring  
- Cloud integration (ThingSpeak)  
- ML-based irrigation prediction  
- Water usage estimation  
- Next irrigation prediction  
- Simple dashboard UI  

---

##  Machine Learning
Models tested:
- Decision Tree  
- Random Forest  (Selected)  
- XGBoost  

Why Random Forest?
- Better accuracy  
- Handles noisy data  
- Stable performance  

---

##  Hardware
- ESP8266  
- Soil Moisture Sensor  
- DHT11 (Temp + Humidity)  
- Rain Sensor  
- Light Sensor (LDR)  
- Relay + Water Pump  

---

##  Tech Stack
- Python  
- Scikit-learn  
- ThingSpeak  
- FastAPI  
- Streamlit  
- Arduino IDE  

---

##  Dashboard
- Live sensor data  
- Irrigation YES/NO  
- Water usage  
- Soil moisture graphs  
- Next irrigation time  

---

## 🚀 Working

1. Data Collection: Sensors continuously collect environmental data such as soil moisture, temperature, and humidity.
2. Data Transmission: The ESP8266 module sends the collected data to the ThingSpeak cloud platform.
3. Data Storage: ThingSpeak securely stores the incoming data for further processing and analysis.
4. Prediction: A machine learning model analyzes the data and predicts the irrigation requirements.
5. Visualization: The processed data and predictions are displayed on a user-friendly dashboard.
6. Control Mechanism: Based on the predictions, the irrigation pump can be automatically or manually controlled.
 

---

##  Setup

### Clone repo
```bash
git clone https://github.com/your-username/smart-agriculture-system.git
cd smart-agriculture-system
