import { useState } from "react";

import SearchForm from "./components/SearchForm";
import CompanyMap from "./components/CompanyMap";

import {
    searchCompanies,
    getRoute
} from "./api";

import type { Company } from "./types";


function App() {

    const [companies, setCompanies] =
        useState<Company[]>([]);

    const [latitude, setLatitude] =
        useState<number | null>(null);

    const [longitude, setLongitude] =
        useState<number | null>(null);

    const [route, setRoute] =
        useState<any | null>(null);

    const [error, setError] =
        useState<string | null>(null);


    async function handleSearch(
        lat: number,
        lon: number,
        radiusKm: number
    ) {

        try {

            setError(null);
            setRoute(null);

            const results =
                await searchCompanies(
                    lat,
                    lon,
                    radiusKm
                );

            setLatitude(lat);
            setLongitude(lon);

            setCompanies(results);

        } catch (error) {

            setError(
                "Failed to search companies."
            );

            console.error(error);
        }
    }


    async function handleCompanyClick(
        company: Company
    ) {

        if (
            latitude === null ||
            longitude === null
        ) {
            return;
        }

        try {

            const result =
                await getRoute(
                    latitude,
                    longitude,
                    company.lat,
                    company.lon
                );

            setRoute(result);

        } catch (error) {

            console.error(error);

            setError(
                "Failed to retrieve route."
            );
        }
    }


    return (

        <main>

            <h1>
                Company Finder
            </h1>


            <SearchForm
                onSearch={handleSearch}
            />


            {error && (

                <p>
                    {error}
                </p>

            )}


            {latitude !== null &&
             longitude !== null && (

                <CompanyMap
                    latitude={latitude}
                    longitude={longitude}
                    companies={companies}
                    route={route}
                    onCompanyClick={
                        handleCompanyClick
                    }
                />

            )}


            <section>

                <h2>
                    Companies Found:{" "}
                    {companies.length}
                </h2>


                {companies.map(company => (

                    <article
                        key={company.company_number}
                    >

                        <h3>
                            {company.company_name}
                        </h3>

                        <p>
                            {
                                company
                                    .registered_office_address
                            }
                        </p>

                        <p>
                            {(
                                company
                                    .distance_metres
                                / 1000
                            ).toFixed(2)}
                            {" "}km away
                        </p>

                    </article>

                ))}

            </section>

        </main>
    );
}


export default App;