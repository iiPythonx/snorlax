import { useEffect, useRef } from "preact/hooks";

import videojs from "video.js";
import type Player from "video.js/dist/types/player";
import { Link } from "wouter";

import "video.js/dist/video-js.css";

import { humanizeTime } from "../lib/time";
import Header from "../components/header";

import { useVideo } from "../hooks/useVideo";
import { useChannel } from "../hooks/useChannel";

function VideoPlayer({ src, poster }: { src: string, poster: string }) {
    const videoReference = useRef<HTMLVideoElement>(null);
    const playerReference = useRef<Player>(null);
    
    useEffect(() => {
        if (!videoReference.current) return;

        playerReference.current = videojs(videoReference.current, {
            controls: true,
            preload: "auto",
            poster,
            sources: [{ src, type: "video/matroska" }]
        })

        return () => {
            if (playerReference.current) playerReference.current.dispose();
        };
    }, [src, poster]);

    return (
        <div data-vjs-player>
            <video className = "video-js" ref = {videoReference} />
        </div>
    );
}

export default function Watch({ id }: { id: string }) {
    const { video, errored: videoError } = useVideo(id);
    const { channel, errored: channelError } = useChannel(video?.channel_id ?? "");

    if (videoError || channelError) return <p>
        Snorlax failed to make an API request for this page.
        <br />
        The video might not exist, or there was a server issue.
    </p>;

    return <>
        <Header />
        {video && channel ? <>
            {(() => {
                let description = video.description.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                description = description.replace(/(https?:\/\/[^\s]+)/g, `<a href = "$1" target = "_blank" rel = "noopener noreferrer">$1</a>`);

                const date = new Date(video.timestamp * 1000);
                const date_string = `${(date.getMonth() + 1).toString().padStart(2, "0")}/${date.getDate().toString().padStart(2, "0")}/${date.getFullYear()}`;

                const videoBaseUrl = `/v1/assets/${video.channel_id}/${video.id}`;

                return <>
                    <h2>{video.title}</h2>
                    <VideoPlayer src = {`${videoBaseUrl}/video.mkv`} poster = {`${videoBaseUrl}/cover.webp`} />
                    <hr />
                    <span>
                        <Link href = {`/channel/${channel.preferred_id}`}>{channel.name}</Link> ({channel.subscribers.toLocaleString()} subscribers) <br />
                        {video.duration_string} • {video.view_count.toLocaleString()} views • {video.like_count.toLocaleString()} likes • {date_string} ({humanizeTime(video.timestamp)})
                    </span>
                    <hr />
                    <pre style = "margin-bottom: 20px;" dangerouslySetInnerHTML = {{ __html: description }}></pre>
                </>;
            })()}
        </> : <span>Loading video information...</span>}
    </>;
}
