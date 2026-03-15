import { useState, useEffect } from "preact/hooks";
import type { Video } from "../types/api";

export function useVideo(id: string) {
    const [video, setVideo] = useState<Video | null>(null);
    const [errored, setErrored] = useState(false);

    useEffect(() => {
        if (!id) return;

        setErrored(false);

        fetch(`/v1/video/${id}`)
            .then(r => {
                if (!r.ok) throw new Error("Failed to fetch video");
                return r.json();
            })
            .then(c => setVideo(c.data))
            .catch(() => setErrored(true));
    }, [id]);

    return { video, errored };
}
