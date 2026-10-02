import {
    MapContainer,
    TileLayer,
    Marker,
    Popup,
    GeoJSON
} from "react-leaflet";

import type { Company } from "../types";

import "leaflet/dist/leaflet.css";


interface CompanyMapProps {

    latitude: number;

    longitude: number;

    companies: Company[];

    route: any | null;

    onCompanyClick: (
        company: Company
    ) => void;
}

function CompanyMap({
    latitude,
    longitude,
    companies,
    route,
    onCompanyClick
}: CompanyMapProps) {


    return (

        <MapContainer
            center={[
                latitude,
                longitude
            ]}
            zoom={10}
            style={{
                height: "600px",
                width: "100%"
            }}
        >

            <TileLayer
                url={
                    `https://maps.geoapify.com/v1/tile/` +
                    `osm-bright/{z}/{x}/{y}.png?` +
                    `apiKey=${import.meta.env.VITE_GEOAPIFY_KEY}`
                }

                attribution={
                    'Powered by Geoapify | ' +
                    '© OpenStreetMap contributors'
                }
            />

            <Marker
                position={[
                    latitude,
                    longitude
                ]}
            >

                <Popup>
                    Search location
                </Popup>

            </Marker>

            {companies.map(company => (

                <Marker
                    key={company.company_number}
                    position={[
                        company.lat,
                        company.lon
                    ]}
                    eventHandlers={{
                        click: () =>
                            onCompanyClick(
                                company
                            )
                    }}
                >
                    <Popup>
                        <strong>
                            {company.company_name}
                        </strong>
                        <br />
                        {company.registered_office_address}
                        <br />
                        Distance:{" "}
                        {(
                            company.distance_metres
                            / 1000
                        ).toFixed(2)} km
                    </Popup>
                </Marker>
            ))}
            {/* Route */}
            {route && (
                <GeoJSON
                    data={route}
                />
            )}
        </MapContainer>
    );
}


export default CompanyMap;