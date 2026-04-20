import os
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =========================================================
# LOAD DATASET
# =========================================================
DATA_URL = "https://github.com/AbidManan/HomeAuto_Ehealth/blob/main/Smart_health_data.csv"
df = pd.read_csv(DATA_URL)

df = df.dropna()
df.columns = df.columns.str.strip()

# =========================================================
# ADD REALISTIC MEDICAL CONTEXT (IMPORTANT IMPROVEMENT)
# =========================================================
np.random.seed(42)

df["Patient_ID"] = np.random.randint(1000, 1100, len(df))
df["Age"] = np.random.randint(60, 85, len(df))  # eldercare realism

# REALISTIC ADMISSION TIME (NOT FAKE 2026 SEQUENCE)
start_time = datetime.now() - timedelta(days=7)
df["Timestamp"] = [start_time + timedelta(minutes=i*5) for i in range(len(df))]

# =========================================================
# BASELINE MODEL (IMPORTANT CLINICAL FEATURE)
# =========================================================
def get_baseline(patient_df):
    return {
        "hr": patient_df["Heart_Rate"].mean(),
        "temp": patient_df["Temperature"].mean(),
        "glu": patient_df["Glucose"].mean(),
        "spo2": patient_df["SpO2"].mean()
    }

# =========================================================
# RISK ENGINE (DEVIATION BASED — REAL CLINICAL STYLE)
# =========================================================
def risk_engine(hr, temp, glu, spo2, baseline):
    risk = 0

    # deviation from baseline matters (VERY IMPORTANT IN MEDICINE)
    if abs(hr - baseline["hr"]) > 20:
        risk += 3
    elif abs(hr - baseline["hr"]) > 10:
        risk += 2

    if abs(temp - baseline["temp"]) > 1.5:
        risk += 3

    if abs(glu - baseline["glu"]) > 40:
        risk += 3

    if spo2 < 92:
        risk += 3

    return risk

# =========================================================
# CONFIDENCE MODEL
# =========================================================
def confidence(risk):
    return min(40 + risk * 10, 98)

# =========================================================
# XAI (MEDICAL STYLE EXPLANATION)
# =========================================================
def xai(hr, temp, glu, spo2, risk, baseline):
    reasons = []

    if abs(hr - baseline["hr"]) > 20:
        reasons.append("Significant heart rate deviation from patient baseline")

    if abs(temp - baseline["temp"]) > 1.5:
        reasons.append("Abnormal temperature trend detected")

    if abs(glu - baseline["glu"]) > 40:
        reasons.append("Glucose instability observed")

    if spo2 < 92:
        reasons.append("Oxygen saturation below safe threshold")

    base = " | ".join(reasons) if reasons else "Stable relative to patient baseline"

    if risk >= 7:
        return "CRITICAL ALERT: " + base
    elif risk >= 4:
        return "MODERATE RISK: " + base
    else:
        return "LOW RISK: " + base

# =========================================================
# ACTION ENGINE
# =========================================================
def action(risk, conf):
    if risk >= 7:
        return "EMERGENCY RESPONSE REQUIRED: Immediate clinical intervention"
    elif risk >= 4:
        return "HIGH PRIORITY: Doctor review recommended"
    else:
        return "ROUTINE CARE: Continue monitoring"

# =========================================================
# DASH APP
# =========================================================
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style={
    "backgroundColor": "#0b1320",
    "color": "white",
    "padding": "20px",
    "fontFamily": "Arial"
}, children=[

    html.H2("Eldercare Health Monitoring  System",
            style={"textAlign": "center"}),

    dcc.Graph(id="graph"),

    html.Div(id="patient-info", style={
        "backgroundColor": "white",
        "color": "black",
        "padding": "15px",
        "marginTop": "10px",
        "borderRadius": "10px"
    }),

    html.Div(id="analysis", style={
        "backgroundColor": "#1c2541",
        "color": "white",
        "padding": "15px",
        "marginTop": "10px",
        "borderRadius": "10px"
    }),

    dcc.Interval(id="interval", interval=2000, n_intervals=0)
])

# =========================================================
# CALLBACK (REALISTIC SIMULATION)
# =========================================================
@app.callback(
    [Output("graph", "figure"),
     Output("patient-info", "children"),
     Output("analysis", "children")],
    Input("interval", "n_intervals")
)
def update(n):

    idx = n % len(df)
    row = df.iloc[idx]

    patient_id = row["Patient_ID"]

    # patient history window
    patient_df = df[df["Patient_ID"] == patient_id].tail(30)

    baseline = get_baseline(patient_df)

    hr = row["Heart_Rate"]
    temp = row["Temperature"]
    glu = row["Glucose"]
    spo2 = row["SpO2"]

    risk = risk_engine(hr, temp, glu, spo2, baseline)
    conf = confidence(risk)

    explanation = xai(hr, temp, glu, spo2, risk, baseline)
    act = action(risk, conf)

    # =========================================================
    # GRAPH (PROFESSIONAL + LABELED)
    # =========================================================
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=patient_df["Timestamp"],
        y=patient_df["Heart_Rate"],
        name="Heart Rate (BPM)"
    ))

    fig.add_trace(go.Scatter(
        x=patient_df["Timestamp"],
        y=patient_df["Temperature"],
        name="Temperature (°C)"
    ))

    fig.add_trace(go.Scatter(
        x=patient_df["Timestamp"],
        y=patient_df["Glucose"],
        name="Glucose (mg/dL)"
    ))

    fig.update_layout(
        title=f"Patient {patient_id} Clinical Trend Analysis",
        xaxis_title="Time (Clinical Timeline)",
        yaxis_title="Physiological Measurements",
        template="plotly_dark"
    )

    # =========================================================
    # PATIENT INFO PANEL
    # =========================================================
    info = f"""
Patient ID: {patient_id}  
Age: {row['Age']} years  
Timestamp: {row['Timestamp']}  

Risk Score: {risk}/10  
Confidence: {conf}%
"""

    # =========================================================
    # ANALYSIS PANEL
    # =========================================================
    analysis = f"""
{explanation}

Clinical Decision:
{act}
"""

    return fig, info, analysis

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
