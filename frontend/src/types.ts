export interface Company{
    company_number: string;
    company_name: string;
    company_type: string;
    registered_office_address: string;
    lat: number;
    lon: number;
    distance_metres: number;
}

export interface SearchLocation {
    lat: number;
    lon: number;
    radiusKm: number;
}