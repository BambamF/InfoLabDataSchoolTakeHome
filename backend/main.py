from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.database import find_companies
from backend.routing import get_route 

app = FastAPI(title="Company Finder API")

app.add_middleware(CORSMiddleware, allow_origins=["https://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/companies")
def companies(lat: float, lon: float, radius_km: float):
    if radius_km <= 0:
        raise HTTPException(status_code=400, detail="Radius must be greated than zero")
    if not -90 <= lat <= 90:
        raise HTTPException(status_code=400, detail="Invalide Latitude")
    if not -180 <= lon <= 180:
        raise HTTPException(status_code=400, detail="Invalid Longitude")
    result = find_companies(lat, lon, radius_km)
    return result.to_dict(orient="records")

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