// Copyright (c) 2026 iiPython

import snorlaxConfig from "../snorlax.toml";

interface SnorlaxConfig {
    snorlax: {
        video_path:    string;
        database_path: string;
    };

    videos: {
        subtitle_languages: string[];
    };
};

export const config = snorlaxConfig as SnorlaxConfig;