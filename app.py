import asyncio
import json
import os

import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AzureOpenAI
from pydantic import BaseModel


load_dotenv()
AZURE_MAPS_BASE = "https://atlas.microsoft.com"
AZURE_MAPS_KEY = os.environ["AZURE_MAPS_KEY"]
ENDPOINT = "https://hackyeah-open-ai.openai.azure.com/"
AGENT_PROMPT_RECOMMENDATION = "You are a calmcation travel expert who provide people useful travel informations. The radius area for places of interest is maximum 3km from the destination place the user wants to go., you must not provide any place outside the 3km radius of the destination coordinates provided. Give back max 3 results ONLY within that radius based on best opinions on those places adding latitute and longitude of those places. Lookup for possible public events in the area in the following 90 days from today. You cannot answer anything more then recommendations about those coordinates. Answer back with a JSON array that contains the following objects {{\"lat\": xxxx, \"lon\": xxxx, \"name\": \"name of the place\",\"events\": [{{\"name\": event 1, \"date\": timestamp}}]}}"
API_KEY = os.environ["AZURE_OPENAI_API_KEY"]

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def fetch(session, url, params, name, events):
    async with session.get(url, params=params) as response:
        res = await response.json()
        res.update({"name": name})
        res.update({"events": events})
        return res


class RecommendationAsk(BaseModel):
    lat: str
    lon: str
    start_lat: str
    start_lon: str
    calmcation: str
    mood: str


client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
)


@app.post("/recommendations")
async def test_route_to_poi(obj: RecommendationAsk):
    response = await asyncio.to_thread(
        client.chat.completions.create,
        messages=[
            {
                "role": "system",
                "content": AGENT_PROMPT_RECOMMENDATION.format(obj.lat, obj.lon, obj.calmcation, obj.mood),
            },
            {
                "role": "user",
                "content": f"I'd like to travel to this coordinates - longitude: {obj.lon} - latitude: {obj.lat}, My mood is {obj.mood}, pick places that are aligned with my actual mood. Those places should be following my calmcation thoughts, which are {obj.calmcation}",
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
                "query": f"{obj.start_lat},{obj.start_lon}:{res['lat']},{res['lon']}",
                "travelMode": "car",
                "traffic": "false"
            }
            tasks.append(
                fetch(
                    session, f"{AZURE_MAPS_BASE}/route/directions/json", params, res["name"], res["events"])
            )
        results = await asyncio.gather(*tasks)

        for result in results:
            final_result = {
                "origin": {"lat": obj.start_lat, "lon": obj.start_lon},
                "destination": result["name"],
                "route_summary": result.get("routes", [])[0].get("summary", {}),
                "legs": result.get("routes", [])[0].get("legs", []),
                "events": result["events"]
            }
            final_results.append(final_result)
    return final_results
