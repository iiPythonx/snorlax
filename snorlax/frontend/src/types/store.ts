export interface Settings {
    languages: string[];
    autoplay: boolean;
    sponsorblock: boolean;
    storeProgress: boolean;
}

export interface Store {
    settings: Settings;
    videoProgress: Record<string, number>;
}
