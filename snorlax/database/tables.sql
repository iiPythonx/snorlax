PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS channels (
    id           TEXT PRIMARY KEY,
    handle       TEXT UNIQUE,
    name         TEXT,
    subscribers  INTEGER,
    preferred_id TEXT GENERATED ALWAYS AS (COALESCE(handle, id)) VIRTUAL
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
    caption_langs   TEXT,  -- JSON
    chapters        TEXT,  -- JSON
    available       BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

CREATE VIEW IF NOT EXISTS videos_w_channel AS
SELECT
    v.*,
    v.rowid AS rowid,
    c.name AS channel_name,
    c.preferred_id AS channel_preferred_id
FROM videos v
JOIN channels c ON v.channel_id = c.id;

-- Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id         TEXT PRIMARY KEY,
    video_id   TEXT NOT NULL,
    status     TEXT,
    progress   INTEGER,
    speed      REAL,
    eta        INTEGER,
    error      TEXT,
    created_at INTEGER
    FOREIGN KEY(video_id) REFERENCES videos(id) ON DELETE CASCADE
);

CREATE VIEW IF NOT EXISTS videos_w_job AS
SELECT
    v.*,
    v.rowid AS rowid,
    c.name AS channel_name,
    c.preferred_id AS channel_preferred_id,
    j.status,
    j.progress,
    j.speed,
    j.eta,
    j.error
FROM videos v
JOIN channels c ON v.channel_id = c.id
LEFT JOIN jobs j ON j.video_id = v.id;

-- Full text search
CREATE VIRTUAL TABLE IF NOT EXISTS videos_fts USING fts5(
    title,
    description,
    channel_name
);

CREATE TRIGGER IF NOT EXISTS video_after_insert AFTER INSERT ON videos BEGIN
    INSERT INTO videos_fts(rowid, title, description, channel_name)
    SELECT
        new.rowid,
        new.title,
        new.description,
        c.name
    FROM channels c
    WHERE c.id = new.channel_id;
END;

CREATE TRIGGER IF NOT EXISTS video_after_delete AFTER DELETE ON videos BEGIN
    DELETE FROM videos_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS video_after_update AFTER UPDATE ON videos BEGIN
    UPDATE videos_fts
    SET
        title = new.title,
        description = new.description,
        channel_name = (
            SELECT name FROM channels WHERE id = new.channel_id
        )
    WHERE rowid = new.rowid;
END;

CREATE TRIGGER IF NOT EXISTS channel_after_name_update AFTER UPDATE OF name ON channels BEGIN
    UPDATE videos_fts
    SET channel_name = new.name
    WHERE rowid IN (
        SELECT rowid FROM videos WHERE channel_id = new.id
    );
END;
