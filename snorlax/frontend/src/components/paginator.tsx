import { useEffect, useState } from "preact/hooks";
import { Link } from "wouter";

import { humanizeTime } from "../lib/time";
import type { Video, Channel, Job } from "../types/api";

type PaginatorProps = {
    type: "video" | "channel" | "job";
    endpoint: string;
    limit?: number;
    params?: Record<string, string>;
};

function VideoItem({ item }: { item: Video }) {
    const video = item as Video;
    const videoBaseUrl = `/v1/assets/${video.channel_id}/${video.id}`;
    return (
        <article key = {video.id}>
            <Link href = {`/watch/${video.id}`} className = "video-poster flex column">
                <img src = {`${videoBaseUrl}/cover.webp`} />
                <span className = "duration-string">{video.duration_string}</span>
                <span>{video.title}</span>
            </Link>
            <div>
                <Link href = {`/channel/${video.channel_preferred_id}`} className = "silent">{video.channel_name}</Link>
                {" "}
                <br />
                <span>
                {video.view_count.toLocaleString()} views • {humanizeTime(video.timestamp)}
                </span>
            </div>
        </article>
    );
}

function ChannelItem({ item }: { item: Channel }) {
    const channel = item as Channel;
    return (
        <article key = {channel.id}>
            <Link href = {`/channel/${channel.preferred_id}`}>{channel.name}</Link>
        </article>
    );
}

function JobItem({ item }: { item: Job }) {
    console.log(item.id);
    return <p>this is supposed to be a job</p>;
}

export default function Paginator({ type, endpoint, limit = 8, params }: PaginatorProps) {
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(1);
    const [items, setItems] = useState<(Video | Channel | Job)[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadTime, setLoadTime] = useState<number | null>(null);

    async function fetchPage() {
        const start = Date.now();
        setLoading(true);

        try {
            const query = params ? "&" + Object.entries(params).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&") : "";
            const response = await fetch(`/v1/${endpoint}?page=${page}&limit=${limit}${query}`);

            const data = (await response.json()).data;
            setItems(data.items);
            setTotal(Math.ceil(data.total / limit));
            setLoadTime(Date.now() - start);
        } catch (err: any) { setItems([]); setTotal(1); } finally { setLoading(false); }
    }

    useEffect(() => {
        fetchPage();
    }, [page, params]);

    return (
        <div className = "flex column">
            <div className = "flex item-list">
                {!loading && items.length === 0 && <span>No results returned from API.</span>}
                {!loading && items.map((item) => {
                    switch (type) {
                        case "video":
                            return <VideoItem key = {item.id} item = {item as Video} />

                        case "channel":
                            return <ChannelItem key = {item.id} item = {item as Channel} />

                        case "job":
                            return <JobItem key = {item.id} item = {item as Job} />
                    }
                })}
            </div>
            <article className = "flex paginator">
                {loadTime !== null && <span className = "api-time">[ {loadTime}ms ]</span>}
                <div>
                    <button onClick = {() => page > 1 && setPage(page - 1)} disabled = {page === 1}>&lt; Back</button>
                    <span> | Page {page} / {total} | </span>
                    <button onClick = {() => page < total && setPage(page + 1)} disabled = {page === total}>Next &gt;</button>
                </div>
            </article>
        </div>
    );
}