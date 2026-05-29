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
    
    # --- DATEN-BEREINIGUNG FÜR DIE GRAPHEN ---
    # Entfernt " €" und Tausenderpunkte, um echte Zahlen zu machen
    for col in ["Hinflug_Günstigster_Markt", "Hinflug_Emirates", "Hinflug_Qatar", 
                "HinRück_Günstigster_Markt", "HinRück_Emirates", "HinRück_Qatar"]:
        df[col + "_clean"] = df[col].astype(str).str.replace(" €", "", regex=False).str.replace(".", "", regex=False).str.strip()
        df[col + "_clean"] = pd.to_numeric(df[col + "_clean"], errors='coerce')

    # Spalten aufteilen für zwei nebeneinanderliegende Graphen
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.subheader("📈 Preisverlauf: Nur Hinflug")
        # Filtert Zeilen ohne gültige Zahlen aus, damit der Graph sauber zeichnet
        df_ow = df.dropna(subset=["Hinflug_Günstigster_Markt_clean"])
        if not df_ow.empty:
            fig_ow = px.line(df_ow, x="Zeitpunkt", y=["Hinflug_Günstigster_Markt_clean", "Hinflug_Emirates_clean", "Hinflug_Qatar_clean"],
                             labels={"value": "Preis in EUR", "Zeitpunkt": "Abfrage-Zeit"},
                             title="Hinflug (12.01.2027)")
            st.plotly_chart(fig_ow, use_container_width=True)
        else:
            st.info("Warte auf den nächsten automatischen Lauf für die Hinflug-Grafik...")

    with graph_col2:
        st.subheader("📉 Preisverlauf: Hin- & Rückflug")
        df_rt = df.dropna(subset=["HinRück_Günstigster_Markt_clean"])
        if not df_rt.empty:
            fig_rt = px.line(df_rt, x="Zeitpunkt", y=["HinRück_Günstigster_Markt_clean", "HinRück_Emirates_clean", "HinRück_Qatar_clean"],
                             labels={"value": "Preis in EUR", "Zeitpunkt": "Abfrage-Zeit"},
                             title="Round-Trip (Rückflug: 13.04.2027)")
            st.plotly_chart(fig_rt, use_container_width=True)
        else:
            st.info("Warte auf den nächsten automatischen Lauf für die Kombi-Grafik...")
    
    st.markdown("---")
    
    # --- DATA TABLE ---
    st.subheader("📋 Rohdaten")
    st.dataframe(df.drop(columns=[c for c in df.columns if "_clean" in c]), use_container_width=True)

else:
    st.warning("Noch keine CSV-Datei mit Daten gefunden. Lass die GitHub Action erst einmal laufen!")
