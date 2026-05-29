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

# Basis-Parameter
base_params = {
    "engine": "google_flights",
    "departure_id": "HAM",
    "arrival_id": "SYD",
    "outbound_date": "2027-01-12",
    "travel_class": "ECONOMY",
    "currency": "EUR",
    "hl": "de",
    "gl": "de",
    "api_key": API_KEY
}

def flugdaten_auswerten(data):
    """Filtert die Flüge flexibler und sicherer nach der Anzahl der echten Flugsegmente"""
    preis_markt = "Kein Flug (max. 1 Stopp)"
    preis_emirates = "Kein Flug (max. 1 Stopp)"
    preis_qatar = "Kein Flug (max. 1 Stopp)"

    alle_flüge = data.get("best_flights", []) + data.get("other_flights", [])
    
    # 1. Günstigster Markt-Preis mit max. 1 Stopp
    for flug in alle_flüge:
        flüge_liste = flug.get("flights", [])
        # Bei Hinflug (OW) max 2 Segmente, bei Round-Trip (RT) sind oft Hin- und Rückflug zusammen in der Liste
        if len(flüge_liste) <= 4:
            # Wir prüfen kurz, ob pro Richtung maximal ein Zwischenstopp drin ist
            # SerpApi liefert bei 'legs' oft die genaue Stopp-Anzahl pro Richtung
            legs = flug.get("legs", [])
            max_stops = max([leg.get("stops", 0) for leg in legs]) if legs else 0
            
            if max_stops <= 1:
                preis_markt = flug.get("price", "N/A")
                break

    # 2. Gezielt nach Emirates & Qatar suchen
    for flug in alle_flüge:
        flüge_liste = flug.get("flights", [])
        ticket_preis = flug.get("price", "N/A")
        
        legs = flug.get("legs", [])
        max_stops = max([leg.get("stops", 0) for leg in legs]) if legs else 0
        
        if max_stops <= 1:
            beteiligte_airlines = [f.get("airline", "").lower() for f in flüge_liste]
            ist_emirates = any("emirates" in a for a in beteiligte_airlines)
            ist_qatar = any("qatar" in a for a in beteiligte_airlines)
            
            if ist_emirates and preis_emirates == "Kein Flug (max. 1 Stopp)":
                preis_emirates = ticket_preis
            if ist_qatar and preis_qatar == "Kein Flug (max. 1 Stopp)":
                preis_qatar = ticket_preis
                    
    return preis_markt, preis_emirates, preis_qatar

try:
    # --- ABFRAGE 1: Nur Hinflug (One-Way) ---
    print("Frage One-Way Flüge an...")
    params_ow = base_params.copy()
    params_ow["type"] = "2"  # STRIKT: 2 bedeutet "One-Way" bei SerpApi!
    response_ow = requests.get(URL, params=params_ow)
    ow_markt, ow_emirates, ow_qatar = flugdaten_auswerten(response_ow.json())

    # --- ABFRAGE 2: Hin- und Rückflug (Round-Trip) ---
    print("Frage Round-Trip Flüge an...")
    params_rt = base_params.copy()
    params_rt["type"] = "1"  # STRIKT: 1 bedeutet "Round-Trip" bei SerpApi!
    params_rt["return_date"] = "2027-05-11"
    response_rt = requests.get(URL, params=params_rt)
    rt_markt, rt_emirates, rt_qatar = flugdaten_auswerten(response_rt.json())

    # --- DATEN SPEICHERN ---
    now = datetime.now()
    zeitpunkt = now.strftime("%Y-%m-%d %H:%M:%S")
    wochentag = now.strftime("%A")

    csv_file = "flugpreise_sydney.csv"
    
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
    
    print("Preise erfolgreich aktualisiert!")

except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")
