export type Chapter = {
    start_time: number;
    title:      string;
    end_time:   number;
}

export type Video = {
    id:                   string;
    title:                string;
    duration:             number;
    view_count:           number;
    timestamp:            number;
    channel_id:           string;
    channel_name:         string;
    channel_preferred_id: string;
    available:            boolean;
};

export type VideoFull = Video & {
    like_count:           number;
    description:          string;
    caption_langs:        string[];
    chapters:             Chapter[];
};

export type Channel = {
    id:           string;
    name:         string;
    handle:       string | null;
    subscribers:  number;
    preferred_id: string;
};

export type Job = Omit<Video, "view_count" | "available"> & {
    job_id:   string;
    status:   "finished" | "downloading" | "remuxing" | "failed";
    progress: number | null;
    speed:    number | null;
    eta:      number | null;
    error:    string | null;
}
