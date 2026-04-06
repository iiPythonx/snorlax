export type Chapter = {
    start_time: number;
    title:      string;
    end_time:   number;
}

export type Video = {
    id:                   string;
    title:                string;
    description:          string;
    view_count:           number;
    like_count:           number;
    duration:             number;
    timestamp:            number;
    channel_id:           string;
    caption_langs:        string[];
    chapters:             Chapter[];
    channel_name:         string;
    channel_preferred_id: string;
    available:            boolean;
};

export type Channel = {
    id:           string;
    name:         string;
    handle:       string | null;
    subscribers:  number;
    preferred_id: string;
};

export type Job = Video & {
    status:   "finished" | "downloading" | "remuxing" | "failed";
    progress: number | null;
    speed:    number | null;
    eta:      number | null;
    error:    string | null;
    job_id:   string;
}
