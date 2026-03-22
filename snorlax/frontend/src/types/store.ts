export interface Settings {
    languages: string[];
    autoplay: boolean;
    storeProgress: boolean;
}

export interface Store {
    settings: Settings;
    videoProgress: Record<string, number>;
}
