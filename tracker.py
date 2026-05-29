import os
import requests
from datetime import datetime
import pandas as pd

# 1. API Setup (Holt sich den Key sicher aus der Umgebung)
API_KEY = os.getenv("SERPAPI_API_KEY")
URL = "https://serpapi.com/search.json"

if not API_KEY:
    print("Fehler: Kein SERPAPI_API_KEY in den Umgebungsvariablen gefunden!")
    exit(1)

# 2. Parameter für deinen Flug nach Sydney (12. Januar 2027)
params = {
    "engine": "google_flights",
    "departure_id": "HAM",
    "arrival_id": "SYD",
    "outbound_date": "2027-01-12",
    "currency": "EUR",
    "hl": "de",
    "gl": "de",
    "api_key": API_KEY
}

try:
    print("Frage Flugdaten bei Google Flights an...")
    response = requests.get(URL, params=params)
    data = response.json()
    
    # 3. Den günstigsten Preis aus den 'Besten Flügen' extrahieren
    best_flights = data.get("best_flights", [])
    if best_flights:
        lowest_price = best_flights[0].get("price", "N/A")
    else:
        lowest_price = "N/A"
        
    # 4. Zeitstempel und Wochentag erstellen
    now = datetime.now()
    zeitpunkt = now.strftime("%Y-%m-%d %H:%M:%S")
    wochentag = now.strftime("%A") # Z.B. Monday, Tuesday...

    # 5. Daten in CSV-Datei schreiben
    csv_file = "flugpreise_sydney.csv"
    df = pd.DataFrame([[zeitpunkt, wochentag, lowest_price]], columns=["Zeitpunkt", "Wochentag", "Preis_EUR"])
    
    # Wenn die Datei noch nicht existiert, mit Header schreiben, sonst anhängen
    file_exists = os.path.exists(csv_file)
    df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
    
    print(f"Erfolgreich geloggt: {zeitpunkt} ({wochentag}) -> {lowest_price}€")

except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")