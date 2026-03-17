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
    duration_string:      string;
    timestamp:            number;
    channel_id:           string;
    caption_langs:        string[];
    chapters:             Chapter[];
    channel_name:         string;
    channel_preferred_id: string;
};

export type Channel = {
    id:           string;
    name:         string;
    handle:       string | null;
    subscribers:  number;
    preferred_id: string;
};
