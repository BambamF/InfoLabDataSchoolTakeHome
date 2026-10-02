import requests

from backend.config import GEOAPIFY_KEY

ROUTING_URL = "https://api.geoapify.com/v1/routing"

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

