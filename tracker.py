import os
import requests
from datetime import datetime
import pandas as pd

# 1. API Setup
API_KEY = os.getenv("SERPAPI_API_KEY")
URL = "https://serpapi.com/search.json"

if not API_KEY:
    print("Fehler: Kein SERPAPI_API_KEY in den Umgebungsvariablen gefunden!")
    exit(1)

def fetch_flights(params):
    try:
        response = requests.get(URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten bei der API-Anfrage: {e}")
        return None

def extract_best_price(data, airline_filter=None):
    if not data:
        return "API-Fehler"
        
    all_flights = data.get("best_flights", []) + data.get("other_flights", [])
    valid_flights = []
    
    for f in all_flights:
        # Lese die Flugsegmente (Legs)
        legs = f.get('flights', [])
        if not legs:
            continue
            
        # Prüfe Airline-Filter (Wenn z.B. Emirates gesucht wird, muss Emirates in mindestens einem der Segmente auftauchen)
        if airline_filter:
            matches_airline = any(airline_filter.lower() in leg.get('airline', '').lower() for leg in legs)
            if not matches_airline:
                continue
                
        price = f.get('price')
        if price is None:
            continue
            
        # Anzahl der Stopps ist näherungsweise die Anzahl der Segmente minus 1
        stops = len(legs) - 1
        
        valid_flights.append({
            'price': price,
            'stops': stops,
            'flight_info': f
        })
        
    if not valid_flights:
        return "Kein Flug"
        
    # Sortiere zuerst nach aufsteigenden Stopps (wenigste Stopps), dann nach aufsteigendem Preis (günstigster)
    valid_flights.sort(key=lambda x: (x['stops'], x['price']))
    
    best = valid_flights[0]
    return f"{best['price']} €"

# 2. Parameter definieren
base_params = {
    "engine": "google_flights",
    "departure_id": "HAM",
    "arrival_id": "SYD",
    "outbound_date": "2027-01-12",
    "currency": "EUR",
    "hl": "de",
    "gl": "de",
    "api_key": API_KEY
}

# Hinflug (One-Way)
oneway_params = base_params.copy()

# Hin- und Rückflug (Round-Trip)
roundtrip_params = base_params.copy()
roundtrip_params["return_date"] = "2027-04-13"

print("Frage One-Way Flugdaten an...")
oneway_data = fetch_flights(oneway_params)

print("Frage Round-Trip Flugdaten an...")
roundtrip_data = fetch_flights(roundtrip_params)

# 3. Günstigste Preise extrahieren (wenigste Stopps -> günstigster Preis)
oneway_markt = extract_best_price(oneway_data)
oneway_emirates = extract_best_price(oneway_data, "Emirates")
oneway_qatar = extract_best_price(oneway_data, "Qatar Airways")

roundtrip_markt = extract_best_price(roundtrip_data)
roundtrip_emirates = extract_best_price(roundtrip_data, "Emirates")
roundtrip_qatar = extract_best_price(roundtrip_data, "Qatar Airways")

# 4. Zeitstempel und Wochentag erstellen
now = datetime.now()
zeitpunkt = now.strftime("%Y-%m-%d %H:%M:%S")
wochentag = now.strftime("%A")

# 5. Daten in CSV-Datei schreiben
csv_file = "flugpreise_sydney.csv"
columns = [
    "Zeitpunkt", "Wochentag", 
    "Hinflug_Günstigster_Markt", "Hinflug_Emirates", "Hinflug_Qatar", 
    "HinRück_Günstigster_Markt", "HinRück_Emirates", "HinRück_Qatar"
]

row = [
    zeitpunkt, wochentag,
    oneway_markt, oneway_emirates, oneway_qatar,
    roundtrip_markt, roundtrip_emirates, roundtrip_qatar
]

df = pd.DataFrame([row], columns=columns)

file_exists = os.path.exists(csv_file)
df.to_csv(csv_file, mode='a', header=not file_exists, index=False)

print(f"\nErfolgreich geloggt: {zeitpunkt} ({wochentag})")
print(f"One-Way   | Markt: {oneway_markt:10} | Emirates: {oneway_emirates:10} | Qatar: {oneway_qatar:10}")
print(f"Roundtrip | Markt: {roundtrip_markt:10} | Emirates: {roundtrip_emirates:10} | Qatar: {roundtrip_qatar:10}")