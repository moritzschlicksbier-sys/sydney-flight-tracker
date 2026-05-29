import os
import requests
from datetime import datetime
import pandas as pd

# 1. API Setup
API_KEY = os.getenv("SERPAPI_API_KEY")
URL = "https://serpapi.com/search.json"

if not API_KEY:
    print("Fehler: Kein SERPAPI_API_KEY gefunden!")
    exit(1)

# Basis-Parameter (Gilt für beide Abfragen)
base_params = {
    "engine": "google_flights",
    "departure_id": "HAM",
    "arrival_id": "SYD",
    "outbound_date": "2027-01-12", # Auf 2027 korrigiert
    "travel_class": "ECONOMY",
    "currency": "EUR",
    "hl": "de",
    "gl": "de",
    "api_key": API_KEY
}

def flugdaten_auswerten(data):
    """Hilfsfunktion, um die Preise für Markt, Emirates und Qatar mit max. 1 Stopp zu filtern"""
    preis_markt = "Kein Flug (max. 1 Stopp)"
    preis_emirates = "Kein Flug (max. 1 Stopp)"
    preis_qatar = "Kein Flug (max. 1 Stopp)"

    alle_flüge = data.get("best_flights", []) + data.get("other_flights", [])
    
    # 1. Günstigster Markt-Preis mit max. 1 Stopp
    for flug in alle_flüge:
        legs = flug.get("legs", [])
        max_stops = max([leg.get("stops", 0) for leg in legs]) if legs else 0
        if max_stops <= 1:
            preis_markt = flug.get("price", "N/A")
            break

    # 2. Emirates & Qatar mit max. 1 Stopp
    for flug in alle_flüge:
        legs = flug.get("legs", [])
        max_stops = max([leg.get("stops", 0) for leg in legs]) if legs else 0
        
        if max_stops <= 1:
            ticket_preis = flug.get("price", "N/A")
            for segment in flug.get("flights", []):
                airline_name = segment.get("airline", "").lower()
                if "emirates" in airline_name and preis_emirates == "Kein Flug (max. 1 Stopp)":
                    preis_emirates = ticket_preis
                if "qatar" in airline_name and preis_qatar == "Kein Flug (max. 1 Stopp)":
                    preis_qatar = ticket_preis
                    
    return preis_markt, preis_emirates, preis_qatar

try:
    # --- ABFRAGE 1: Nur Hinflug (One-Way) ---
    print("Frage One-Way Flüge an...")
    params_ow = base_params.copy()
    response_ow = requests.get(URL, params=params_ow)
    ow_markt, ow_emirates, ow_qatar = flugdaten_auswerten(response_ow.json())

    # --- ABFRAGE 2: Hin- und Rückflug (Round-Trip) ---
    print("Frage Round-Trip Flüge an...")
    params_rt = base_params.copy()
    params_rt["return_date"] = "2027-05-11" # Dein Rückflugdatum
    response_rt = requests.get(URL, params=params_rt)
    rt_markt, rt_emirates, rt_qatar = flugdaten_auswerten(response_rt.json())

    # --- DATEN SPEICHERN ---
    now = datetime.now()
    zeitpunkt = now.strftime("%Y-%m-%d %H:%M:%S")
    wochentag = now.strftime("%A")

    csv_file = "flugpreise_sydney.csv"
    
    # Alle 6 Preise in eine strukturierte Zeile packen
    neue_daten = [[
        zeitpunkt, wochentag, 
        ow_markt, ow_emirates, ow_qatar, 
        rt_markt, rt_emirates, rt_qatar
    ]]
    
    spalten = [
        "Zeitpunkt", "Wochentag", 
        "Hinflug_Günstigster_Markt", "Hinflug_Emirates", "Hinflug_Qatar",
        "HinRück_Günstigster_Markt", "HinRück_Emirates", "HinRück_Qatar"
    ]
    
    df = pd.DataFrame(neue_daten, columns=spalten)
    file_exists = os.path.exists(csv_file)
    df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
    
    print(f"Erfolgreich alle 6 Preise geloggt für {zeitpunkt} ({wochentag})!")

except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")
