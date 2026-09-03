// Copyright (c) 2026 iiPython

import { Database } from "bun:sqlite";

import SQL from "./tables.sql" with { type: "text" };
import { Channel, PaginatedResult, Video, VideoWithChannel } from "./schema";

const SEARCH_VALID_TOKENS = /[^a-zA-Z0-9 ]/g;

export class SnorlaxDB {
    private db: Database;

    constructor() {
        this.db = new Database("snorlax.db");
        this.init();
    }

    public close(): void {
        this.db.run("PRAGMA wal_checkpoint(TRUNCATE);");
        this.db.close();
    }

    private async init(): Promise<void> {
        this.db.run(SQL);

        // Populate FTS
        const ftsHasSomething = this.db.query("SELECT 1 FROM videos_fts LIMIT 1").get();
        if (!ftsHasSomething) {
            this.db.run(`
                INSERT INTO videos_fts(rowid, title, description, channel_name)
                SELECT v.rowid, v.title, v.description, c.name
                FROM videos v
                JOIN channels c ON c.id = v.channel_id;
            `);
        }
    }

    private parseVideoRow<T extends Video>(row: Record<string, any>): T {
        return {
            ...row,
            available: Boolean(row.available),
            caption_langs: row.caption_langs ? JSON.parse(row.caption_langs) : [],
            chapters: row.chapters ? JSON.parse(row.chapters) : []
        } as T
    }

    // Channels
    public addChannel(channel: Omit<Channel, "preferred_id">): boolean {
        return this.db.prepare(`
            INSERT OR IGNORE INTO channels (id, handle, name, subscribers)
            VALUES ($id, $handle, $name, $subscribers)
        `).run({
            $id: channel.id,
            $handle: channel.handle,
            $name: channel.name,
            $subscribers: channel.subscribers
        }).changes > 0;
    }

    public getChannel(channelId: string): Channel | null {
        return this.db
            .query<Channel, [string, string]>("SELECT * FROM channels WHERE id = ?1 OR handle = ?2")
            .get(channelId, channelId);
    }

    public getChannels(limit = 20, page = 1): PaginatedResult<Channel> {
        return {
            items: this.db
                .query<Channel, [number, number]>("SELECT * FROM channels ORDER BY name ASC LIMIT ?1 OFFSET ?2")
                .all(limit, (page - 1) * limit),
            total: this.db
                .query<{ total: number }, []>("SELECT COUNT(*) as total FROM channels")
                .get()?.total ?? 0
        };
    }

    public deleteChannel(channelId: string): void {
        this.db.query("DELETE FROM channels WHERE id = ?").run(channelId);
    }

    // Videos
    public addVideo(video: Video): boolean {
        return this.db.prepare(`
            INSERT OR IGNORE INTO videos (
                id, title, duration, view_count, timestamp, 
                channel_id, available, like_count, description, 
                caption_langs, chapters
            ) VALUES (
                $id, $title, $duration, $view_count, $timestamp, 
                $channel_id, $available, $like_count, $description, 
                $caption_langs, $chapters
            )
        `).run({
            $id: video.id,
            $title: video.title,
            $duration: video.duration,
            $view_count: video.view_count,
            $timestamp: video.timestamp,
            $channel_id: video.channel_id,
            $available: video.available ? 1 : 0,
            $like_count: video.like_count ?? 0,
            $description: video.description ?? "",
            $caption_langs: JSON.stringify(video.caption_langs ?? []),
            $chapters: JSON.stringify(video.chapters ?? [])
        }).changes > 0;
    }

    public getVideo(videoId: string): VideoWithChannel | null {
        const row = this.db
            .query<Record<string, any>, [string]>("SELECT * FROM videos_w_channel WHERE id = ?")
            .get(videoId);

        return row ? this.parseVideoRow<VideoWithChannel>(row) : null
    }

    public getVideos(options: {
        query?: string
        channelId?: string
        limit?: number
        page?: number
    }): PaginatedResult<VideoWithChannel> {
        const limit = options.limit ?? 20;
        const page = options.page ?? 1;
        const offset = (page - 1) * limit;

        let filters: string[] = ["available = 1"];
        let params: Record<string, any> = { $limit: limit, $offset: offset };
        let fromClause = "videos_w_channel v";

        // FTS
        if (options.query) {
            const sanitized = options.query.replace(SEARCH_VALID_TOKENS, "").trim()
            if (!sanitized) return { items: [], total: 0 };

            fromClause = "videos_fts f JOIN videos_w_channel v ON v.rowid = f.rowid";
            filters.push("videos_fts MATCH $ftsQuery");
            params.$ftsQuery = sanitized.split(/\s+/).map((w) => `${w}*`).join(" ");
        }

        if (options.channelId) {
            filters.push("v.channel_id = $channelId");
            params.$channelId = options.channelId;
        }

        const where = filters.join(" AND ");

        // Fetch
        return {
            items: this.db.query<Record<string, any>, any>(`
                SELECT v.* FROM ${fromClause}
                WHERE ${where}
                ORDER BY ${options.query ? "bm25(videos_fts)" : "v.timestamp DESC"}
                LIMIT $limit OFFSET $offset
            `).all(params).map((r) => this.parseVideoRow<VideoWithChannel>(r)),
            total: this.db.query<{ total: number }, any>(`
                SELECT COUNT(*) as total FROM ${fromClause}
                WHERE ${where}
            `).get(params)?.total ?? 0
        };
    }
}