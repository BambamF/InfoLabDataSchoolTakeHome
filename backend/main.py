from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database import find_companies
from backend.routing import get_route, geocode_postcode

app = FastAPI(title="Company Finder API")

app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/companies")
def companies(
    postcode: str,
    radius_km: float
):
    if radius_km <= 0:
        raise HTTPException(
            status_code=400,
            detail="Radius must be greater than zero."
        )

    location = geocode_postcode(postcode)

    if location is None:
        raise HTTPException(
            status_code=404,
            detail="Postcode could not be found."
        )

    result = find_companies(
        location["longitude"],
        location["latitude"],
        radius_km
    )

    return {
        "location": location,
        "companies": result.to_dict(orient="records")
    }

@app.get("/route")
def route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float):
    try:
        return get_route(
            origin_lat,
            origin_lon,
            dest_lat,
            dest_lon
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Routing request failed: {str(e)}")