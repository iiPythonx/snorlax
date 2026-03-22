import { useEffect, useState } from "preact/hooks";
import type { TargetedInputEvent } from "preact";

import { useStore } from "../hooks/useStore";

const VALID_LANGUAGES = [

    // English
    "en", "en-US", "en-GB",

    // Spanish
    "es", "es-ES", "es-MX",

    // Portugese
    "pt", "pt-BR", "pt-PT",

    // Chinese
    "zh", "zh-CN", "zh-TW",

    // French
    "fr", "fr-CA",

    // Everything else
    "de", "it", "ru", "ja", "ko", "ar", "hi"
];

const INTL = new Intl.DisplayNames("en-US", { type: "language" });

export default function Settings() {
    const [store, updateStore] = useStore();
    const [selectedLanguages, setSelectedLanguages] = useState<string[]>(store.settings.languages);
    const [input, setInput] = useState<string>(() => selectedLanguages.join(", "));

    useEffect(() => {
        updateStore(store => { store.settings.languages = selectedLanguages; })
    }, [selectedLanguages]);

    const handleLanguageUpdate = (e: TargetedInputEvent<HTMLInputElement>) => {
        const value = (e.target as HTMLInputElement).value;
        const languages = value.split(",").map(v => v.trim());

        setInput(value);
        setSelectedLanguages([...new Set(languages.filter((lang) => VALID_LANGUAGES.includes(lang)))]);
    }

    return <>
        <h2>Settings</h2>
        <fieldset className = "flex column">
            <legend>Preferred Languages</legend>
            <span>Please enter the default caption language you would like. You can add multiple, ordered by preference, by separating them with a comma.</span>
            <span>Keep in mind that English (en) is not the same as American English (en-US), for example.</span>
            <input type = "text" onChange={handleLanguageUpdate} placeholder = "en-US, en-GB, en" value = {input} />
            <span>Preview: {selectedLanguages.map((lang) => INTL.of(lang)).join(", ") || "none selected"}</span>
        </fieldset>
        <fieldset className = "flex column">
            <legend>General Options</legend>
            <label>
                <input
                    type = "checkbox"
                    checked = {store.settings.storeProgress}
                    onChange = {(e) => {
                        updateStore(store => { store.settings.storeProgress = e.currentTarget.checked; })
                    }}
                />
                <span>Save video progress</span>
            </label>
            <label>
                <input
                    type = "checkbox"
                    checked = {store.settings.autoplay}
                    onChange = {(e) => {
                        updateStore(store => { store.settings.autoplay = e.currentTarget.checked; })
                    }}
                />
                <span>Auto play videos</span>
            </label>
            <label>
                <input
                    type = "checkbox"
                    checked = {store.settings.sponsorblock}
                    onChange = {(e) => {
                        updateStore(store => { store.settings.sponsorblock = e.currentTarget.checked; })
                    }}
                />
                <span>Enable sponsorblock</span>
            </label>
        </fieldset>
    </>;
}
