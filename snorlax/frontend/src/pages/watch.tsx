import { useEffect, useRef, useState } from "preact/hooks";
import { Link, useLocation } from "wouter";

import type Player from "video.js/dist/types/player";

import "video.js/dist/video-js.css";
import videojs from "video.js";
import "videojs-hotkeys";

import { createDurationString, humanizeTime } from "../lib/time";

import { useAsset } from "../hooks/useAsset";
import type { Chapter } from "../types/api";
import { useHeaderActions } from "../hooks/useHeaderActions";
import { usePageTitle } from "../hooks/usePageTitle";
import { useStore } from "../hooks/useStore";
import type Component from "video.js/dist/types/component";

type Caption = {
    src:     string;
    kind:    string;
    srclang: string;
    label:   string;
    default: boolean;
}

const INTL = new Intl.DisplayNames("en-US", { type: "language" });

function VideoPlayer({ src, poster, id, chapters, captions }: { src: string, poster: string, id: string, chapters: Chapter[], captions: Caption[] }) {
    const videoReference = useRef<HTMLVideoElement>(null);
    const playerReference = useRef<Player | null>(null);
    const [store, updateStore] = useStore();
    const [player, setPlayer] = useState<Player | null>(null);

    useEffect(() => {
        if (!videoReference.current) return;

        const videoInstance = videojs(videoReference.current as HTMLVideoElement, {
            controls: true,
            preload: "auto",
            poster,
            sources: [{ src, type: "video/matroska" }],
            tracks: captions,
            plugins: {
                hotkeys: {
                    enableModifiersForNumbers: false,
                    alwaysCaptureHotkeys: true,
                    captureDocumentHotkeys: true,
                    documentHotkeysFocusElementFilter: (e: HTMLElement) => e.tagName.toLowerCase() === "body",
                    enableVolumeScroll: false
                }
            },
            autoplay: store.settings.autoplay
        });

        playerReference.current = videoInstance;
        setPlayer(videoInstance);

        return () => {
            playerReference.current?.dispose();
            playerReference.current = null;
            setPlayer(null);
        };
    }, [src, poster]);

    // Time tracking
    if (store.settings.storeProgress) {
        useEffect(() => {
            if (!player) return;
            player.on("loadedmetadata", () => {
                const duration = player.duration() || 0;

                // Grab the current video time
                // If we're at the end of a video (last 10 seconds), don't bother skipping
                const existingTime = store.videoProgress[id] || 0;
                if (existingTime < duration - 10) player.currentTime(existingTime);

                setInterval(() => {
                    const time = Math.round(player.currentTime() || 0);
                    if (time !== store.videoProgress[id]) updateStore((store) => store.videoProgress[id] = time);
                }, 1000);
            });
        }, [player]);
    }

    // Sponsorblock
    if (store.settings.sponsorblock) {
        useEffect(() => {
            if (!player) return;

            let segments: { segment: [number, number] }[] = [];
            const fetchSegments = async () => {
                const response = await fetch(`https://sponsor.ajay.app/api/skipSegments?videoID=${id}`);
                if (response.status !== 200) return;

                segments = await response.json();
            };

            fetchSegments();

            const onTimeUpdate = () => {
                const time = player.currentTime() || 0;
                for (const seg of segments) {
                    const [start, end] = seg.segment;
                    if (time >= start && time < end) {
                        player.currentTime(end);
                        break;
                    }
                }
            };

            player.on("timeupdate", onTimeUpdate);
            return () => player.off("timeupdate", onTimeUpdate);
        }, [player, id]);
    }

    // Handle chapters
    if (chapters.length) {
        useEffect(() => {
            if (!player) return;

            player.on("loadedmetadata", () => {
                const total = player.duration();
                const seekBar = player.getDescendant("controlBar", "progressControl", "seekBar");
                if (!total || !seekBar) return;
    
                for (const chapter of chapters) {
                    const left = (chapter.start_time / total) * 100 + "%";
                    seekBar.el().append(videojs.dom.createEl("div", undefined, {
                        class: "vjs-marker",
                        style: `left: ${left}`,
                    }));
                }
            });
    
            const timeControl = player.getDescendant([
                "controlBar",
                "progressControl",
                "seekBar",
                "mouseTimeDisplay",
                "timeTooltip",
            ]) as Component & { update: (rect: DOMRect, point: number, time: string) => void, write: (time: string) => void };
            timeControl.update = function (_: DOMRect, point: number, time: string) {
                const currentTime = point * (player.duration() || 0);
                const currentChapter = chapters.findIndex(({ end_time }) => end_time >= currentTime);
    
                if (currentChapter > -1) {
                    const { title } = chapters[currentChapter];
    
                    videojs.dom.emptyEl(this.el());
                    return videojs.dom.appendContent(this.el(), [
                        videojs.dom.createEl("strong", undefined, undefined, title),
                        videojs.dom.createEl("span", undefined, undefined, `(${time})`)
                    ]);
                }
    
                this.write(time);
            };
        }, [player])
    }

    return (
        <div data-vjs-player>
            <video className = "video-js" ref = {videoReference} />
        </div>
    );
}

export default function Watch({ id }: { id: string }) {
    const { asset: video, done: videoLoaded } = useAsset(id, "video");
    const { asset: channel, done: channelLoaded } = useAsset(video?.channel_id ?? "", "channel");

    const { setActions } = useHeaderActions();
    const [, navigate] = useLocation();
    const [store,] = useStore();

    if (!(video && channel)) return videoLoaded && channelLoaded ? <p>
        Snorlax failed to make an API request for this page.
        <br />
        This indicates either the video or channel doesn't exist, or there was a server issue.
    </p> : null;

    useEffect(() => {
        setActions([
            {
                label: "Remove Video",
                onClick: async () => {
                    await fetch(`/v1/video/${id}`, { method: "DELETE" });
                    navigate("/");
                },
            },
        ]);
        return () => setActions([]);
    }, [id]);

    usePageTitle(video.title || null);

    // Load description
    let description = video.description.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    description = description.replace(/(https?:\/\/[^\s]+)/g, `<a href = "$1" target = "_blank" rel = "noopener noreferrer">$1</a>`);

    // Timestamping
    const date = new Date(video.timestamp * 1000);
    const date_string = `${(date.getMonth() + 1).toString().padStart(2, "0")}/${date.getDate().toString().padStart(2, "0")}/${date.getFullYear()}`;

    // Base URL for captions, stream, poster
    const videoBaseUrl = `/v1/assets/${video.channel_id}/${video.id}`;

    // Handle captions
    const selected = store.settings.languages.find(lang => video.caption_langs.includes(lang));
    const captions = video.caption_langs ? video.caption_langs.map((code) => ({
        kind: "captions",
        src: `${videoBaseUrl}/sub.${code}.vtt`,
        srclang: code,
        label: INTL.of(code) || code,
        default: code === selected
    })) : [];

    return <>
        <h2>{video.title}</h2>
        <VideoPlayer
            src = {`${videoBaseUrl}/video.mkv`}
            poster = {`${videoBaseUrl}/cover.webp`}
            id = {id}
            chapters = {video.chapters}
            captions = {captions}
        />
        <hr />
        <span>
            <Link href = {`/channel/${channel.preferred_id}`}>{channel.name}</Link> ({channel.subscribers.toLocaleString()} subscribers) <br />
            {createDurationString(video.duration)} • {video.view_count.toLocaleString()} views • {video.like_count.toLocaleString()} likes • {date_string} ({humanizeTime(video.timestamp)})
        </span>
        <hr />
        <pre style = "margin-bottom: 20px;" dangerouslySetInnerHTML = {{ __html: description }}></pre>
    </>;
}
