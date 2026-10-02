import requests

from backend.config import GEOAPIFY_KEY

ROUTING_URL = "https://api.geoapify.com/v1/routing"

GEOCODING_URL = "https://api.geoapify.com/v1/geocode/search"

def get_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float):
    waypoints = f"{origin_lat},{origin_lon}|{dest_lat}{dest_lon}"
    params = {
        "waypoints": waypoints,
        "mode": "drive",
        "format": "geojson",
        "apiKey": GEOAPIFY_KEY
    }

    response = requests.get(ROUTING_URL, params=params, timeout=30)

    response.raise_for_status()

    return response.json()

def geocode_postcode(postcode: str):
    params = {
        "text": postcode,
        "apiKey": GEOAPIFY_KEY,
        "format": "json"
    }

    response = requests.get(
        GEOCODING_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        return None

    return {
        "latitude": results[0]["lat"],
        "longitude": results[0]["lon"],
        "formatted": results[0].get("formatted", postcode)
    }
