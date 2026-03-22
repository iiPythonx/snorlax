import { useState } from "preact/hooks";
import type { Store } from "../types/store";

const DEFAULTS: Store = {
    settings: {
        languages: [],
        autoplay: false,
        sponsorblock: true,
        storeProgress: false
    },
    videoProgress: {}
};

let cache: Store | null = null;

function deepMerge<T extends object>(base: T, obj: Partial<T>): T {
    const result: any = { ...base };
    const keys = new Set([...Object.keys(base), ...Object.keys(obj || {})]);

    for (const key of keys) {
        const baseVal = base[key as keyof T];
        const objVal = obj?.[key as keyof T];

        if (baseVal && typeof baseVal === "object" && !Array.isArray(baseVal) &&
            objVal && typeof objVal === "object" && !Array.isArray(objVal)) {
            result[key] = deepMerge(baseVal, objVal);
        } else result[key] = objVal !== undefined ? objVal : baseVal;
    }

    return result as T;
}

function loadStore(): Store {
    if (cache) return cache;
    try {
        const raw = localStorage.getItem("settings");
        const parsed: Partial<Store> = raw ? JSON.parse(raw) : {};
        cache = deepMerge(DEFAULTS, parsed);
    } catch { cache = structuredClone(DEFAULTS); }
    return cache
}

function saveStore(): void {
    if (!cache) return;
    localStorage.setItem("settings", JSON.stringify(cache));
}

function updateStore(mutator: (store: Store) => void): void {
    const store = loadStore();
    mutator(store);
    saveStore();
}

export function useStore(): [Store, (mutator: (store: Store) => void) => void] {
    const [state, setState] = useState<Store>(() => loadStore());
    function update(mutator: (store: Store) => void) {
        updateStore(mutator);
        setState({ ...loadStore() });
    }
    return [state, update];
}
