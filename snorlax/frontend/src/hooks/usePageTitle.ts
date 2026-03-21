import { useEffect } from "preact/hooks";

export function usePageTitle(title: string | null) {
    useEffect(() => {
        document.title = title || "snorlax";
        return () => { document.title = "snorlax"; };
    }, [title]);
}

