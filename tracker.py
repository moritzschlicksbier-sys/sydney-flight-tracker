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

    # Google Flights liefert Ergebnisse in 'best_flights' und 'other_flights'
    alle_flüge = data.get("best_flights", []) + data.get("other_flights", [])
    
    # 1. Günstigster Markt-Preis mit max. 1 Stopp
    for flug in alle_flüge:
        flüge_liste = flug.get("flights", [])
        
        # Ein Hinflug mit 1 Stopp besteht aus genau 2 Flugsegmenten
        # Bei Round-Trips liefert SerpApi oft den Gesamtpreis, wir prüfen hier die Segmente der ersten Hälfte
        if len(flüge_liste) <= 2:
            preis_markt = flug.get("price", "N/A")
            break

    # 2. Gezielt nach Emirates & Qatar suchen
    for flug in alle_flüge:
        flüge_liste = flug.get("flights", [])
        ticket_preis = flug.get("price", "N/A")
        
        # Finde heraus, welche Airlines an diesem gesamten Flug beteiligt sind
        beteiligte_airlines = [f.get("airline", "").lower() for f in flüge_liste]
        
        # Wir filtern alle Flüge raus, die insgesamt mehr als 2 Segmente für den Hinflug haben (sprich > 1 Stopp)
        # Da SerpApi bei Roundtrips manchmal alle Segmente (Hin + Rück) in eine Liste wirft, 
        # prüfen wir hier flexibel, ob Emirates oder Qatar das Hauptsegment fliegt
        ist_emirates = any("emirates" in a for a in beteilte_airlines)
        ist_qatar = any("qatar" in a for a in beteilte_airlines)
        
        # Zähle die Stopps anhand der Segmente
        # Wenn es ein reiner Hinflug ist, darf die Liste max. 2 Elemente haben. 
        # Wenn es ein Roundtrip ist, hat sie oft max. 4 Elemente (2 hin, 2 zurück).
        anzahl_segmente = len(flüge_liste)
        
        if anzahl_segmente <= 4:  # Schließt Flüge mit 2 oder mehr Stopps pro Richtung aus
            if ist_emirates and preis_emirates == "Kein Flug (max. 1 Stopp)":
                preis_emirates = ticket_preis
            if ist_qatar and preis_qatar == "Kein Flug (max. 1 Stopp)":
                preis_qatar = ticket_preis
                    
    return preis_markt, preis_emirates, preis_qatar

try:
    # --- ABFRAGE 1: Nur Hinflug ---
    print("Frage One-Way Flüge an...")
    params_ow = base_params.copy()
    response_ow = requests.get(URL, params=params_ow)
    ow_markt, ow_emirates, ow_qatar = flugdaten_auswerten(response_ow.json())

    # --- ABFRAGE 2: Hin- und Rückflug ---
    print("Frage Round-Trip Flüge an...")
    params_rt = base_params.copy()
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
