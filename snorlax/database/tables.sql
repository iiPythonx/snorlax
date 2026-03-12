CREATE TABLE IF NOT EXISTS channels (
    id          TEXT PRIMARY KEY,
    handle      TEXT UNIQUE,
    name        TEXT,
    subscribers INTEGER
);

CREATE TABLE IF NOT EXISTS videos (
    id              TEXT PRIMARY KEY,
    title           TEXT,
    description     TEXT,
    view_count      INTEGER,
    like_count      INTEGER,
    duration_string TEXT,
    timestamp       INTEGER,
    channel_id      TEXT,
    caption_langs   TEXT,
    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

CREATE VIEW IF NOT EXISTS videos_w_channel AS
SELECT
    v.*,
    c.name AS channel_name,
    c.handle as channel_handle
FROM videos v
JOIN channels c ON v.channel_id = c.id;
