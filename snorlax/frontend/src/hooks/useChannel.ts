import { useState, useEffect } from "preact/hooks";
import type { Channel } from "../types/api";

export function useChannel(id: string) {
    const [channel, setChannel] = useState<Channel | null>(null);
    const [errored, setErrored] = useState(false);

    useEffect(() => {
        if (!id) return;

        setErrored(false);

        fetch(`/v1/channel/${id}`)
            .then(r => {
                if (!r.ok) throw new Error("Failed to fetch channel");
                return r.json();
            })
            .then(c => setChannel(c.data))
            .catch(() => setErrored(true));
    }, [id]);

    return { channel, errored };
}
