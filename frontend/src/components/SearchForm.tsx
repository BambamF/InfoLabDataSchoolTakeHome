import { useState } from "react";

interface SearchFormProps {
    onSearch: (
        lat: number,
        lon: number,
        radiusKm: number
    ) => void;
}

function SearchForm({onSearch}: SearchFormProps){
    const [lat, setLat] = useState("");
    const [lon, setLon] = useState("");
    const [radius, setRadius] = useState("10");

    function handleSubmit(event: React.FormEvent){
        event.preventDefault();
        const latitude = Number(lat)
        const longitude = Number(lon)
        const radiusKm = Number(radius)

        if (Number.isNaN(latitude) || Number.isNaN(longitude) || Number.isNaN(radiusKm)){
            return;
        }

        onSearch(latitude, longitude, radiusKm);
    }

    return (
        <form onSubmit={handleSubmit}>
            <label>
                Latitude
                <input type="number" step="any" value={lat} onChange={event => setLat(event.target.value)}/>
            </label>
            <label>
                Longitude
                <input type="number" step="any" value={lon} onChange={event => setLon( event.target.value )}/>
            </label>
             <label> Radius (km)
                <input type="number" min="0.1" step="0.1" value={radius} onChange={event => setRadius( event.target.value )}/>
            </label>
            <button type="submit">
                Search
            </button>
        </form>
    );
}

export default SearchForm;