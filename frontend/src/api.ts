import type { Company } from "./types";

const API_URL = "https://localhost:8000";

export async function searchCompanies(lat: number, lon: number, radiusKm: number): Promise<Company[]>{
    const params = new URLSearchParams({
        lat: lat.toString(),
        lon: lon.toString(),
        radiusKm: radiusKm.toString()
    });

    const response = await fetch(`${API_URL}/companies?${params}`);

    if (!response.ok){
        throw new Error("Failed to search companies");
    }

    return response.json();
}

export async function getRoute(origin_lat: number,
                                origin_lon: number,
                                dest_lat: number,
                                dest_lon: number
){
    const params = new URLSearchParams({
        origin_lat: origin_lat.toString(),
        origin_lon: origin_lon.toString(),
        dest_lat: dest_lat.toString(),
        dest_lon: dest_lon.toString()
    });

    const response = await fetch(`${API_URL}/route?${params}`);

    if (!response.ok){
        throw new Error("Failed to retrieve route");
    }

    return response.json();

}