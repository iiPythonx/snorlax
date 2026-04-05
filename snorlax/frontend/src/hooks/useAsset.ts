import { useState, useEffect } from "preact/hooks";
import type { Video, Channel } from "../types/api";

type AssetMap = {
    video: Video;
    channel: Channel;
}

export function useAsset<T extends keyof AssetMap>(id: string, type: T) {
    const [asset, setAsset] = useState<AssetMap[T] | null>(null);
    const [done, setDone] = useState<boolean>(false);

    if (!id) return { asset, done: true };

    useEffect(() => {
        fetch(`/v1/${type}/${id}`)
            .then(r => {
                if (!r.ok) throw new Error(`Failed to fetch ${type}`);
                return r.json();
            })
            .then(c => setAsset(c.data))
            .catch(() => {})
            .finally(() => setDone(true));
    }, [id, type]);

    return { asset, done };
}
