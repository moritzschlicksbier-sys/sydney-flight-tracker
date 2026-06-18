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
    
    # Letzte Zeile für Metriken extrahieren
    letzte_zeile = df.iloc[-1]
    
    # Hinflug Airline bestimmen
    ow_markt = letzte_zeile["Hinflug_Günstigster_Markt"]
    if ow_markt == letzte_zeile["Hinflug_Emirates"]:
        ow_airline = "Airline: Emirates"
    elif ow_markt == letzte_zeile["Hinflug_Qatar"]:
        ow_airline = "Airline: Qatar Airways"
    else:
        ow_airline = "Airline: Andere Airline"

    # Hin- & Rückflug Airline bestimmen
    rt_markt = letzte_zeile["HinRück_Günstigster_Markt"]
    if rt_markt == letzte_zeile["HinRück_Emirates"]:
        rt_airline = "Airline: Emirates"
    elif rt_markt == letzte_zeile["HinRück_Qatar"]:
        rt_airline = "Airline: Qatar Airways"
    else:
        rt_airline = "Airline: Andere Airline"
        
    # --- METRIKEN (Kacheln) ---
    st.subheader("📊 Aktuelle Preislage")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="Günstigster Hinflug im Ganzen Markt", value=ow_markt, delta=ow_airline, delta_color="off")
    with col2:
        st.metric(label="Günstigster Hin- und Rückflug Markt", value=rt_markt, delta=rt_airline, delta_color="off")
        
    st.markdown("---")
    
    # --- DATEN-BEREINIGUNG FÜR DIE GRAPHEN ---
    # Entfernt " €" und Tausenderpunkte, um echte Zahlen zu machen
    for col in ["Hinflug_Günstigster_Markt", "Hinflug_Emirates", "Hinflug_Qatar", 
                "HinRück_Günstigster_Markt", "HinRück_Emirates", "HinRück_Qatar"]:
        df[col + "_clean"] = df[col].astype(str).str.replace(" €", "", regex=False).str.replace(".", "", regex=False).str.strip()
        df[col + "_clean"] = pd.to_numeric(df[col + "_clean"], errors='coerce')

    color_map = {
        "Hinflug_Günstigster_Markt_clean": "#00CC00",  # Deutliches Grün
        "Hinflug_Emirates_clean": "#D71921",           # Emirates Rot
        "Hinflug_Qatar_clean": "#87CEFA",              # Hellblau für Qatar
        "HinRück_Günstigster_Markt_clean": "#00CC00",
        "HinRück_Emirates_clean": "#D71921",
        "HinRück_Qatar_clean": "#87CEFA"
    }

    # Spalten aufteilen für zwei nebeneinanderliegende Graphen
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.subheader("📈 Preisverlauf: Nur Hinflug")
        # Filtert Zeilen ohne gültige Zahlen aus, damit der Graph sauber zeichnet
        df_ow = df.dropna(subset=["Hinflug_Günstigster_Markt_clean"])
        if not df_ow.empty:
            fig_ow = px.line(df_ow, x="Zeitpunkt", y=["Hinflug_Günstigster_Markt_clean", "Hinflug_Emirates_clean", "Hinflug_Qatar_clean"],
                             labels={"value": "Preis in EUR", "Zeitpunkt": "Abfrage-Zeit", "variable": "Airline"},
                             color_discrete_map=color_map,
                             title="Hinflug (12.01.2027)")
            
            # Linien etwas dicker machen für modernen Look
            fig_ow.update_traces(line=dict(width=4))
            
            # Platz für die Logos am Rand schaffen
            fig_ow.update_layout(margin=dict(r=80))
            
            # Mittelgroße Linie rechts für aktuelle Preise von Emirates und Qatar
            last_ek_ow = df_ow["Hinflug_Emirates_clean"].dropna().iloc[-1] if not df_ow["Hinflug_Emirates_clean"].dropna().empty else None
            last_qr_ow = df_ow["Hinflug_Qatar_clean"].dropna().iloc[-1] if not df_ow["Hinflug_Qatar_clean"].dropna().empty else None
            
            if last_ek_ow is not None:
                fig_ow.add_layout_image(
                    source="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Emirates_logo.svg/320px-Emirates_logo.svg.png",
                    xref="x domain", yref="y",
                    x=1.05, y=last_ek_ow,
                    sizex=0.1, sizey=20,
                    xanchor="center", yanchor="middle"
                )
            if last_qr_ow is not None:
                fig_ow.add_layout_image(
                    source="https://upload.wikimedia.org/wikipedia/en/thumb/2/29/Qatar_Airways_Logo.svg/320px-Qatar_Airways_Logo.svg.png",
                    xref="x domain", yref="y",
                    x=1.05, y=last_qr_ow,
                    sizex=0.1, sizey=20,
                    xanchor="center", yanchor="middle"
                )
            st.plotly_chart(fig_ow, use_container_width=True)
        else:
            st.info("Warte auf den nächsten automatischen Lauf für die Hinflug-Grafik...")

    with graph_col2:
        st.subheader("📉 Preisverlauf: Hin- & Rückflug")
        df_rt = df.dropna(subset=["HinRück_Günstigster_Markt_clean"])
        if not df_rt.empty:
            fig_rt = px.line(df_rt, x="Zeitpunkt", y=["HinRück_Günstigster_Markt_clean", "HinRück_Emirates_clean", "HinRück_Qatar_clean"],
                             labels={"value": "Preis in EUR", "Zeitpunkt": "Abfrage-Zeit", "variable": "Airline"},
                             color_discrete_map=color_map,
                             title="Round-Trip (Rückflug: 13.04.2027)")
            
            # Linien etwas dicker machen
            fig_rt.update_traces(line=dict(width=4))
            
            # Platz für die Logos am Rand schaffen
            fig_rt.update_layout(margin=dict(r=80))

            # Mittelgroße Linie rechts
            last_ek_rt = df_rt["HinRück_Emirates_clean"].dropna().iloc[-1] if not df_rt["HinRück_Emirates_clean"].dropna().empty else None
            last_qr_rt = df_rt["HinRück_Qatar_clean"].dropna().iloc[-1] if not df_rt["HinRück_Qatar_clean"].dropna().empty else None
            
            if last_ek_rt is not None:
                fig_rt.add_layout_image(
                    source="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Emirates_logo.svg/320px-Emirates_logo.svg.png",
                    xref="x domain", yref="y",
                    x=1.05, y=last_ek_rt,
                    sizex=0.1, sizey=20,
                    xanchor="center", yanchor="middle"
                )
            if last_qr_rt is not None:
                fig_rt.add_layout_image(
                    source="https://upload.wikimedia.org/wikipedia/en/thumb/2/29/Qatar_Airways_Logo.svg/320px-Qatar_Airways_Logo.svg.png",
                    xref="x domain", yref="y",
                    x=1.05, y=last_qr_rt,
                    sizex=0.1, sizey=20,
                    xanchor="center", yanchor="middle"
                )
            st.plotly_chart(fig_rt, use_container_width=True)
        else:
            st.info("Warte auf den nächsten automatischen Lauf für die Kombi-Grafik...")
    
    st.markdown("---")
    
    # --- DATA TABLE ---
    st.subheader("📋 Rohdaten")
    st.dataframe(df.drop(columns=[c for c in df.columns if "_clean" in c]), use_container_width=True)

else:
    st.warning("Noch keine CSV-Datei mit Daten gefunden. Lass die GitHub Action erst einmal laufen!")
