import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

# Set up SQLite connection
conn = sqlite3.connect('nts_zone_comp_logs.db', check_same_thread=False)
cursor = conn.cursor()

# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS nts_shift_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    line TEXT,
    temp_f REAL,
    humidity INTEGER,
    filler_speed INTEGER,
    zone1_comp REAL,
    zone2_comp REAL,
    zone3_comp REAL,
    zone4_comp REAL,
    zone5_comp REAL,
    ai_percent INTEGER,
    success_flag TEXT,
    notes TEXT
)
""")
conn.commit()

st.title("NTS Zone Comp Tool")

# Sidebar input
with st.sidebar:
    st.header("Input Your Shift Conditions")
    selected_line = st.selectbox("Line", ["L1", "L2"])
    temp = st.slider("Ambient Temp (°F)", 60.0, 80.0, 70.0, step=0.1)
    humidity = st.slider("Humidity (%)", 30, 80, 50)
    filler_speed = st.slider("Filler Speed (bpm)", 900, 1200, 1075)
    ai_percent = st.slider("AI (%)", 80, 100, 96)
    success_flag = st.selectbox("Success?", ["Yes", "No"])
    notes = st.text_area("Notes (optional)")

# Sample historical data (mock)
data = {
    "Line": ["L1", "L1", "L1", "L2", "L2", "L2"],
    "Zone": [1, 2, 3, 1, 2, 3],
    "Temp (F)": [70, 72, 74, 68, 69, 71],
    "Humidity (%)": [50, 52, 48, 55, 54, 50],
    "Filler Speed (bpm)": [1075, 1080, 1090, 1060, 1050, 1075],
    "Zone Comp": [0.3, 0.32, 0.34, 0.28, 0.27, 0.29],
    "Success Rate (%)": [98, 95, 96, 93, 94, 97]
}
df = pd.DataFrame(data)

# Recommendation engine
st.header(f"Zone Comp Recommendations for {selected_line}")
results = []

for zone in range(1, 6):
    df_line = df[(df['Line'] == selected_line) & (df['Zone'] == zone)]
    if df_line.empty:
        results.append({"Zone": zone, "Recommended Comp": "N/A", "Success Rate": "N/A", "Match": "No historical match"})
        continue

    df_line['Total Diff'] = (
        np.abs(df_line['Temp (F)'] - temp) * 0.4 +
        np.abs(df_line['Humidity (%)'] - humidity) * 0.3 +
        np.abs(df_line['Filler Speed (bpm)'] - filler_speed) * 0.3
    )
    best = df_line.sort_values("Total Diff").iloc[0]
    results.append({
        "Zone": zone,
        "Recommended Comp": best["Zone Comp"],
        "Success Rate": best["Success Rate (%)"],
        "Match": f"{best['Temp (F)']}°F, {best['Humidity (%)']}%, {best['Filler Speed (bpm)']} bpm"
    })

recommend_df = pd.DataFrame(results)
st.dataframe(recommend_df)

# Save log to database
if st.button("💾 Save Shift Log"):
    now = datetime.now()
    cursor.execute("""
        INSERT INTO nts_shift_logs (
            date, time, line, temp_f, humidity, filler_speed,
            zone1_comp, zone2_comp, zone3_comp, zone4_comp, zone5_comp,
            ai_percent, success_flag, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now.date(), now.strftime("%H:%M:%S"), selected_line, temp, humidity, filler_speed,
        recommend_df.iloc[0]["Recommended Comp"] if recommend_df.iloc[0]["Recommended Comp"] != "N/A" else None,
        recommend_df.iloc[1]["Recommended Comp"] if recommend_df.iloc[1]["Recommended Comp"] != "N/A" else None,
        recommend_df.iloc[2]["Recommended Comp"] if recommend_df.iloc[2]["Recommended Comp"] != "N/A" else None,
        recommend_df.iloc[3]["Recommended Comp"] if recommend_df.iloc[3]["Recommended Comp"] != "N/A" else None,
        recommend_df.iloc[4]["Recommended Comp"] if recommend_df.iloc[4]["Recommended Comp"] != "N/A" else None,
        ai_percent, success_flag, notes
    ))
    conn.commit()
    st.success("Shift data saved successfully!")
