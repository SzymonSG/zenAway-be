from fastapi import FastAPI
import requests
import os
from dotenv import load_dotenv

load_dotenv()
AZURE_MAPS_BASE = "https://atlas.microsoft.com"

app = FastAPI()

@app.get("/test-route-to-poi")
def test_route_to_poi():
    # Hardkodowana lokalizacja startowa (Rynek Główny, Kraków)
    origin_lat = 50.06143
    origin_lon = 19.93658
    poi_type = "restaurant"

    # 1. Szukamy najbliższej restauracji
    search_url = f"{AZURE_MAPS_BASE}/search/poi/json"
    search_params = {
        "api-version": "1.0",
        "subscription-key": AZURE_MAPS_KEY,
        "query": poi_type,
        "lat": origin_lat,
        "lon": origin_lon,
        "limit": 1
    }

    search_response = requests.get(search_url, params=search_params)
    if search_response.status_code != 200:
        return {"error": "Nie udało się znaleźć POI"}

    results = search_response.json().get("results", [])
    if not results:
        return {"error": "Brak wyników POI"}

    destination = results[0]["position"]
    dest_lat = destination["lat"]
    dest_lon = destination["lon"]

    # 2. Wyznaczamy trasę z uwzględnieniem traffic
    route_url = f"{AZURE_MAPS_BASE}/route/directions/json"
    route_params = {
        "api-version": "1.0",
        "subscription-key": AZURE_MAPS_KEY,
        "query": f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}",
        "travelMode": "car",
        "traffic": "true"
    }

    route_response = requests.get(route_url, params=route_params)
    if route_response.status_code != 200:
        return {"error": "Nie udało się wyznaczyć trasy"}

    return {
        "origin": {"lat": origin_lat, "lon": origin_lon},
        "destination": results[0]["poi"]["name"],
        "route_summary": route_response.json().get("routes", [])[0].get("summary", {}),
        "legs": route_response.json().get("routes", [])[0].get("legs", [])
    }



# http://localhost:8000/test-route-to-poi

# from fastapi import FastAPI, Query
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()

# AZURE_MAPS_KEY = os.getenv("AZURE_MAPS_KEY")
# AZURE_MAPS_BASE = "https://atlas.microsoft.com"

# app = FastAPI()

# @app.get("/route-to-poi")
# def route_to_poi(
#     origin_lat: float = Query(...),
#     origin_lon: float = Query(...),
#     poi_type: str = Query("coffee shop")
# ):
#     # 1. Szukamy najbliższego POI
#     search_url = f"{AZURE_MAPS_BASE}/search/poi/json"
#     search_params = {
#         "api-version": "1.0",
#         "subscription-key": AZURE_MAPS_KEY,
#         "query": poi_type,
#         "lat": origin_lat,
#         "lon": origin_lon,
#         "limit": 1
#     }

#     search_response = requests.get(search_url, params=search_params)
#     if search_response.status_code != 200:
#         return {"error": "Nie udało się znaleźć POI"}

#     results = search_response.json().get("results", [])
#     if not results:
#         return {"error": "Brak wyników POI"}

#     destination = results[0]["position"]
#     dest_lat = destination["lat"]
#     dest_lon = destination["lon"]

#     # 2. Wyznaczamy trasę z uwzględnieniem traffic
#     route_url = f"{AZURE_MAPS_BASE}/route/directions/json"
#     route_params = {
#         "api-version": "1.0",
#         "subscription-key": AZURE_MAPS_KEY,
#         "query": f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}",
#         "travelMode": "car",
#         "traffic": "true"
#     }

#     route_response = requests.get(route_url, params=route_params)
#     if route_response.status_code != 200:
#         return {"error": "Nie udało się wyznaczyć trasy"}

#     return {
#         "destination": results[0]["poi"]["name"],
#         "route": route_response.json()
#     }