import { createContext } from "preact";
import { useContext } from "preact/hooks";
import type { HeaderAction } from "../types/header";

type HeaderActionContextType = {
    actions: HeaderAction[];
    setActions: (actions: HeaderAction[]) => void;
};

export const HeaderActionContext = createContext<HeaderActionContextType>({
    actions: [],
    setActions: () => {},
});

export const useHeaderActions = () => useContext(HeaderActionContext);
