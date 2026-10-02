import { useState } from "react";

interface SearchFormProps {
    onSearch: (
        postcode: string,
        radiusKm: number
    ) => void;
}

function SearchForm({onSearch}: SearchFormProps){
    const [postcode, setPostCode] = useState("");
    const [radius, setRadius] = useState("10");

    function handleSubmit(event: React.SubmitEvent){
        event.preventDefault();
        const radiusKm = Number(radius)

        if (postcode.trim() === "" || Number.isNaN(radiusKm) || radiusKm <= 0){
            return;
        }

        onSearch(postcode.trim(), radiusKm);
    }

    return (
        <form onSubmit={handleSubmit}>
            <label>
                Postcode
                <input type="text" placeholder="e.g N5 2GD" value={postcode} onChange={event => setPostCode(event.target.value)}/>
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