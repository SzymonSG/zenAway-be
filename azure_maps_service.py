import asyncio
import json
import os

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import AzureOpenAI
from pydantic import BaseModel


load_dotenv()
AZURE_MAPS_BASE = "https://atlas.microsoft.com"
AZURE_MAPS_KEY = os.environ["AZURE_MAPS_KEY"]
ENDPOINT = "https://hackyeah-open-ai.openai.azure.com/"
AGENT_PROMPT_RECOMMENDATION = "You are a travel expert who provide people useful informations about places at the given coordinates: lat {} lon: {} in a radius of max 3km\nGiven the categoeris: {} ,give back max 3 results based on best opinions on those places adding latitute and longitude of those places. You cannot answer anything more then recommendations about those coors. Answer back with a JSON array that contains the following objects {{\"lat\": xxxx, \"lon\": xxxx, \"name\": \"name of the place\"}}"
API_KEY = os.environ["AZURE_OPENAI_API_KEY"]

app = FastAPI()


async def fetch(session, url, params, name):
    async with session.get(url, params=params) as response:
        print(f"Fetching {url}")
        res = await response.json()
        res.update({"name": name})
        return res


class RecommendationAsk(BaseModel):
    lat: str
    lon: str
    start_lat: str
    start_lon: str
    categories: list


client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
)


@app.post("/test-route-to-poi")
async def test_route_to_poi(obj: RecommendationAsk):
    response = await asyncio.to_thread(
        client.chat.completions.create,
        messages=[
            {
                "role": "system",
                "content": AGENT_PROMPT_RECOMMENDATION.format(obj.lat, obj.lon, obj.categories),
            },
            {
                "role": "user",
                "content": f"I am interested into this place: longitude: {obj.lon} - latitude: {obj.lat}",
            }
        ],
        max_completion_tokens=16384,
        model="o4-mini"
    )
    results = json.loads(response.choices[0].message.content)

    if not results:
        return {"error": "Brak wyników POI"}

    final_results = []

    async with aiohttp.ClientSession() as session:
        tasks = []
        for res in results:
            params = {
                "api-version": "1.0",
                "subscription-key": AZURE_MAPS_KEY,
                "query": f"{obj.lat},{obj.lon}:{res['lat']},{res['lon']}",
                "travelMode": "car",
                "traffic": "true"
            }
            tasks.append(
                fetch(
                    session, f"{AZURE_MAPS_BASE}/route/directions/json", params, res["name"])
            )
        results = await asyncio.gather(*tasks)

        for result in results:
            final_result = {
                "origin": {"lat": obj.start_lat, "lon": obj.start_lon},
                "destination": result["name"],
                "route_summary": result.get("routes", [])[0].get("summary", {}),
                "legs": result.get("routes", [])[0].get("legs", [])
            }
            final_results.append(final_result)
    return final_results


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
