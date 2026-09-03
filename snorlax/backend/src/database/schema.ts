// Copyright (c) 2026 iiPython

export interface Channel {
    id:            string;
    handle:        string | null;
    name:          string;
    subscribers:   number;
    preferred_id?: string;
}

export interface Video {
    id:             string;
    title:          string;
    duration:       number;
    view_count:     number;
    timestamp:      number;
    channel_id:     string;
    available:      boolean;
    like_count?:    number;
    description?:   string;
    caption_langs?: string[];               // JSON
    chapters?:      Record<string, any>[];  // JSON
}

export interface VideoWithChannel extends Video {
    channel_name:         string;
    channel_preferred_id: string;
}

export interface Job {
    id:         string;
    video_id:   string;
    url:        string;
    status:     "queued" | "processing" | "finished" | "failed";
    progress?:  number;
    speed?:     string;
    eta?:       number;
    error?:     string;
    created_at: string;
}

export interface PaginatedResult<T> {
    items: T[];
    total: number;
}
