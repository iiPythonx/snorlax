import { useEffect, useMemo, useState } from "preact/hooks";
import Paginator from "../components/paginator";

export default function Search() {
    const [query, setQuery] = useState("");
    const [debouncedQuery, setDebouncedQuery] = useState("");

    useEffect(() => {
        const timeout = setTimeout(() => setDebouncedQuery(query), 300);
        return () => clearTimeout(timeout);
    }, [query]);

    const params = useMemo(() => ({ query: debouncedQuery }), [debouncedQuery]);

    return <>
        <main>
            <input
                type = "text"
                placeholder = "Search for anything"
                value = {query}
                autocomplete = "off"
                onInput = {(e: any) => setQuery(e.target.value)}
                autofocus
            />
            <hr />
            <h2>Results</h2>
            <Paginator type = "video" endpoint = "videos" params = {params} />
        </main>
    </>;
}
