import os
import requests
from datetime import datetime
import pandas as pd

# 1. API Setup & Schutz gegen Leerzeichen
RAW_KEY = os.getenv("SERPAPI_API_KEY")
API_KEY = RAW_KEY.strip() if RAW_KEY else None
URL = "https://serpapi.com/search.json"

if not API_KEY:
    print("❌ FEHLER: Kein SERPAPI_API_KEY in den GitHub Secrets gefunden!")
    exit(1)

# Basis-Parameter mit deinen neu entdeckten Filtern!
base_params = {
    "engine": "google_flights",
    "departure_id": "HAM",
    "arrival_id": "SYD",
    "outbound_date": "2027-01-12",
    "travel_class": 1,  # 1 = Economy
    "stops": 2,         # 🚀 NEU: Strikt maximal 1 Zwischenstopp (aus Doku)
    "sort_by": 2,       # 🚀 NEU: Strikt nach Preis sortieren (aus Doku)
    "currency": "EUR",
    "hl": "de",
    "gl": "de",
    "api_key": API_KEY
}

def flugdaten_auswerten(data, info_label):
    if "error" in data:
        print(f"❌ SerpAPI Fehler bei {info_label}: {data['error']}")
        return "API-Fehler", "API-Fehler", "API-Fehler"

    preis_markt = "Kein Flug (max. 1 Stopp)"
    preis_emirates = "Kein Flug (max. 1 Stopp)"
    preis_qatar = "Kein Flug (max. 1 Stopp)"

    # Da wir sort_by=2 nutzen, ist diese Liste schon perfekt vom günstigsten zum teuersten Flug sortiert!
    alle_flüge = data.get("best_flights", []) + data.get("other_flights", [])
    
    if alle_flüge:
        # Der allererste Flug ist automatisch der absolut günstigste auf dem Markt mit max 1 Stopp
        erster_preis = alle_flüge[0].get("price")
        if erster_preis:
            preis_markt = f"{erster_preis} €" if isinstance(erster_preis, int) else erster_preis

        # Jetzt gehen wir die sortierte Liste durch, um Emirates & Qatar abzugreifen
        for flug in alle_flüge:
            current_price = flug.get("price", "N/A")
            if current_price == "N/A":
                continue
            
            # Formatieren, falls es eine reine Zahl ist
            formatted_price = f"{current_price} €" if isinstance(current_price, int) else current_price
            flug_info_text = str(flug).lower()
            
            # Da die Liste nach Preis sortiert ist, ist der ERSTE Treffer automatisch der günstigste für die jeweilige Airline
            if ("emirates" in flug_info_text or "'ek'" in flug_info_text) and preis_emirates == "Kein Flug (max. 1 Stopp)":
                preis_emirates = formatted_price
            
            if ("qatar" in flug_info_text or "'qr'" in flug_info_text) and preis_qatar == "Kein Flug (max. 1 Stopp)":
                preis_qatar = formatted_price
                                
    return preis_markt, preis_emirates, preis_qatar

try:
    # --- ABFRAGE 1: Nur Hinflug (One-Way) ---
    print("🛫 Starte Abfrage für One-Way Flüge...")
    params_ow = base_params.copy()
    params_ow["type"] = 2  # 2 = One-Way
    response_ow = requests.get(URL, params=params_ow)
    ow_markt, ow_emirates, ow_qatar = flugdaten_auswerten(response_ow.json(), "One-Way")

    # --- ABFRAGE 2: Hin- und Rückflug (Round-Trip) ---
    print("🛬 Starte Abfrage für Round-Trip Flüge...")
    params_rt = base_params.copy()
    params_rt["type"] = 1  # 1 = Round-Trip
    params_rt["return_date"] = "2027-05-11"
    response_rt = requests.get(URL, params=params_rt)
    rt_markt, rt_emirates, rt_qatar = flugdaten_auswerten(response_rt.json(), "Round-Trip")

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
    
    print("✅ CSV-Datei erfolgreich mit echten Daten aktualisiert!")

except Exception as e:
    print(f"❌ Fehler: {e}")
