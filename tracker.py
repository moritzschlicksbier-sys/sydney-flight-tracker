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
    preis_markt = "Kein Flug (max. 1 Stopp)"
    preis_emirates = "Kein Flug (max. 1 Stopp)"
    preis_qatar = "Kein Flug (max. 1 Stopp)"

    # Kombiniere alle Flüge, die Google Flights zurückgibt
    alle_flüge = data.get("best_flights", []) + data.get("other_flights", [])
    
    # 1. Günstigster Markt-Preis generell mit max. 1 Stopp
    for flug in alle_flüge:
        legs = flug.get("legs", [])
        # Prüfen, ob irgendein Teil der Reise mehr als 1 Stopp hat
        max_stops = max([leg.get("stops", 0) for leg in legs]) if legs else 0
        
        if max_stops <= 1:
            if "price" in flug:
                preis_markt = f"{flug['price']} €" if isinstance(flug['price'], int) else flug['price']
                break

    # 2. Gezielt nach Emirates & Qatar suchen
    for flug in alle_flüge:
        legs = flug.get("legs", [])
        max_stops = max([leg.get("stops", 0) for leg in legs]) if legs else 0
        
        if max_stops <= 1:
            current_price = flug.get("price", "N/A")
            if current_price == "N/A":
                continue
                
            # Textsuche über alle Flugsegmente hinweg
            flug_info_text = str(flug).lower()
            
            # Emirates Check (Sucht nach 'emirates' oder dem Airline-Code 'ek')
            if ("emirates" in flug_info_text or "'ek'" in flug_info_text) and preis_emirates == "Kein Flug (max. 1 Stopp)":
                preis_emirates = f"{current_price} €" if isinstance(current_price, int) else current_price
            
            # Qatar Check (Sucht nach 'qatar' oder dem Airline-Code 'qr')
            if ("qatar" in flug_info_text or "'qr'" in flug_info_text) and preis_qatar == "Kein Flug (max. 1 Stopp)":
                preis_qatar = f"{current_price} €" if isinstance(current_price, int) else current_price
                    
    return preis_markt, preis_emirates, preis_qatar

try:
    # --- ABFRAGE 1: Nur Hinflug (One-Way) ---
    print("Frage One-Way Flüge an...")
    params_ow = base_params.copy()
    params_ow["type"] = "2"
    response_ow = requests.get(URL, params=params_ow)
    ow_markt, ow_emirates, ow_qatar = flugdaten_auswerten(response_ow.json())

    # --- ABFRAGE 2: Hin- und Rückflug (Round-Trip) ---
    print("Frage Round-Trip Flüge an...")
    params_rt = base_params.copy()
    params_rt["type"] = "1"
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
