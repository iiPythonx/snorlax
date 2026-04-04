import { useEffect, useImperativeHandle, useState } from "preact/hooks";
import { Link } from "wouter";

import { createDurationString, humanizeTime } from "../lib/time";
import type { Video, Channel, Job } from "../types/api";
import { forwardRef } from "preact/compat";

type ViewProps = {
    type:         "video" | "channel" | "job";
    endpoint:     string;
    limit?:       number;
    params?:      Record<string, string>;
    refreshTime?: number;
    onJobCancel?: (job: Job) => void;
};

export type ViewHandle = {
    refresh: () => void;
}

function VideoItem({ item }: { item: Video }) {
    const video = item as Video;
    const videoBaseUrl = `/v1/assets/${video.channel_id}/${video.id}`;
    return <>
        <Link href = {`/watch/${video.id}`} className = "video-poster flex column">
            <img src = {`${videoBaseUrl}/cover.webp`} />
            <span className = "duration-string">{createDurationString(video.duration)}</span>
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
    </>;
}

function ChannelItem({ item }: { item: Channel }) {
    const channel = item as Channel;
    return (
        <Link href = {`/channel/${channel.preferred_id}`}>{channel.name}</Link>
    );
}

function JobItem({ item, onJobCancel }: { item: Job, onJobCancel?: (job: Job) => void }) {
    const finished = ["finished", "failed"].includes(item.status);
    const completed_amount = Math.round(20 * (item.progress / 100));
    const progress_spacing = 20 - completed_amount;

    return <>
        <div className = "flex">
            <Link href = {`/watch/${item.id}`}>{item.title}</Link>
            <button className = "pad-left" onClick = {() => onJobCancel && onJobCancel(item)}>{finished ? "Remove" : "Cancel"} Job</button>
        </div>
        <div className = "flex">
            <Link href = {`/channel/${item.channel_preferred_id}`}>{item.channel_name}</Link> •
            {" "}{humanizeTime(item.timestamp)} • {item.status} {item.status === "downloading" && `• ${item.speed} MiB/s • ETA ${item.eta}s`}
            <pre className = "pad-left">[{"=".repeat(completed_amount)}{" ".repeat(progress_spacing)}] <span style = {{ width: "30px", display: "inline-block", textAlign: "right" }}>{item.progress}%</span></pre>
        </div>
        <br />
        <hr />
    </>
}

const View = forwardRef<ViewHandle, ViewProps>(({
    type, endpoint, limit = 8, params, refreshTime, onJobCancel
}, ref) => {
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
            setTotal(Math.ceil(data.total / limit) || 1);
            setLoadTime(Date.now() - start);
        } catch (err: any) { setItems([]); setTotal(1); } finally { setLoading(false); }
    }

    useEffect(() => {
        fetchPage();
        if (refreshTime) {
            const interval = setInterval(() => fetchPage(), refreshTime * 1000);
            return () => clearInterval(interval);
        }
    }, [refreshTime, page, params]);

    useImperativeHandle(ref, () => ({
        refresh: fetchPage
    }));

    return (
        <div className = "flex column">
            <div className = "flex item-list">
                {!loading && items.length === 0 && <span>No results returned from API.</span>}
                {!loading && items.map((item) => <article key = {item.id} className = {`item-${type}`}>
                    {
                        type === "video" ? <VideoItem item = {item as Video} /> :
                        type === "channel" ? <ChannelItem item = {item as Channel} /> :
                        type === "job" ? <JobItem item = {item as Job} onJobCancel = {onJobCancel} /> :
                        null
                    }
                </article>)}
            </div>
            <article className = "flex view">
                {loadTime !== null && <span className = "api-time">[ {loadTime}ms ]</span>}
                <div>
                    <button onClick = {() => page > 1 && setPage(page - 1)} disabled = {page === 1}>&lt; Back</button>
                    <span> | Page {page} / {total} | </span>
                    <button onClick = {() => page < total && setPage(page + 1)} disabled = {page === total}>Next &gt;</button>
                </div>
            </article>
        </div>
    );
});

export default View;
