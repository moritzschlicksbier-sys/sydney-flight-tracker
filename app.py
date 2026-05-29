import streamlit as pd
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Seitenkonfiguration (Styling)
st.set_page_config(page_title="Sydney Flugpreis Tracker", page_icon="🛫", layout="wide")

st.title("🛫 Sydney Flugpreis-Analyse (HAM -> SYD)")
st.markdown("Dieses Dashboard wertet die täglich gesammelten Preise für den Abflug am 12.01.2027 aus.")

csv_file = "flugpreise_sydney.csv"

if os.path.exists(csv_file):
    # Daten einlesen
    df = pd.read_csv(csv_file)
    
    # Letztes Update anzeigen
    letztes_update = df["Zeitpunkt"].iloc[-1]
    st.success(f"🔄 Letztes Update der Daten: {letztes_update}")
    
    # --- METRIKEN (Kacheln) ---
    st.subheader("📊 Aktuelle Preislage")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Günstigster Hinflug (Markt)", value=df["Hinflug_Günstigster_Markt"].iloc[-1])
    with col2:
        st.metric(label="Hin- & Rückflug (Emirates)", value=df["HinRück_Emirates"].iloc[-1])
    with col3:
        st.metric(label="Hin- & Rückflug (Qatar)", value=df["HinRück_Qatar"].iloc[-1])
        
    st.markdown("---")
    
    # --- CHART 1: Hinflug-Verlauf ---
    st.subheader("📈 Preisentwicklung: Nur Hinflug (12.01.2027)")
    # Bereinige Euro-Zeichen für den Graphen
    for col in ["Hinflug_Günstigster_Markt", "Hinflug_Emirates", "Hinflug_Qatar"]:
        df[col + "_clean"] = df[col].astype(str).str.replace(" €", "").str.replace(",", ".").errors="ignore"
        df[col + "_clean"] = pd.to_numeric(df[col + "_clean"], errors='coerce')
        
    fig_ow = px.line(df, x="Zeitpunkt", y=["Hinflug_Günstigster_Markt_clean", "Hinflug_Emirates_clean", "Hinflug_Qatar_clean"],
                     labels={"value": "Preis in EUR", "Zeitpunkt": "Abfrage-Zeit"},
                     title="One-Way Preise im Zeitverlauf")
    st.plotly_chart(fig_ow, use_container_width=True)
    
    # --- DATA TABLE ---
    st.subheader("📋 Rohdaten")
    st.dataframe(df, use_container_width=True)

else:
    st.warning("Noch keine CSV-Datei mit Daten gefunden. Lass die GitHub Action erst einmal laufen!")
