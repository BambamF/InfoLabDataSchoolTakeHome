
const API_URL = "http://localhost:8000";

export async function searchCompanies(
    postcode: string,
    radiusKm: number
) {
    const params = new URLSearchParams({
        postcode,
        radius_km: radiusKm.toString()
    });

    const response = await fetch(
        `${API_URL}/companies?${params}`
    );

    if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
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