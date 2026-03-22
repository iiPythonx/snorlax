import type { Store } from "../types/store";

const DEFAULTS: Store = {
    settings: {
        languages: [],
        autoplay: false,
        storeProgress: false
    },
    videoProgress: {}
};

let cache: Store | null = null;

function deepMerge<T>(base: T, obj: Partial<T>): T {
    const result = { ...base };
    for (const key in base) {
        const baseVal = base[key];
        const objVal = obj[key];

        if (typeof baseVal === "object" && baseVal !== null && !Array.isArray(baseVal)) result[key] = deepMerge(baseVal, objVal ?? {});
        else result[key] = (objVal ?? baseVal) as T[typeof key];
    }
    return result;
}

export function loadStore(): Store {
    if (cache) return cache;
    try {
        const raw = localStorage.getItem("settings");
        const parsed: Partial<Store> = raw ? JSON.parse(raw) : {};
        cache = deepMerge(DEFAULTS, parsed);
    } catch { cache = structuredClone(DEFAULTS); }
    return cache
}

let timeout: number | undefined;

export function saveStore(): void {
    if (!cache) return;

    clearTimeout(timeout);
    timeout = window.setTimeout(() => {
        localStorage.setItem("settings", JSON.stringify(cache));
    }, 300);
}

export function getStore(): Store {
    return loadStore();
}

export function updateStore(mutator: (store: Store) => void): void {
    const store = loadStore();
    mutator(store);
    saveStore();
}

export function patchStore(patch: Partial<Store>): void {
    const store = loadStore();
    cache = deepMerge(store, patch);
    saveStore();
}
