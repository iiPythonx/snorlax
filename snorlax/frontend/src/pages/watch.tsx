import { useEffect, useRef } from "preact/hooks";
import { Link } from "wouter";

import type Player from "video.js/dist/types/player";
import type Component from "video.js/dist/types/component";

import "video.js/dist/video-js.css";

import { humanizeTime } from "../lib/time";
import Header from "../components/header";

import { useVideo } from "../hooks/useVideo";
import { useChannel } from "../hooks/useChannel";
import type { Chapter } from "../types/api";

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
    const playerReference = useRef<Player>(null);

    useEffect(() => {
        if (!videoReference.current) return;

        let cancelled = false;
        import("video.js").then(async (module) => {
            if (cancelled) return;
            
            await import("videojs-hotkeys");
            
            const videojs = module.default;
            const player = playerReference.current = videojs(videoReference.current as HTMLVideoElement, {
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
                }
            });

            // Handle chapters
            if (chapters.length) {
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
            }

            // Sponsorblock
            const response = await fetch(`https://sponsor.ajay.app/api/skipSegments?videoID=${id}`);
            if (response.status === 200) {
                const segments: { segment: [number, number] }[] = await response.json();
                player.on("timeupdate", () => {
                    const time = player.currentTime() || 0;
                    for (const seg of segments) {
                        const [start, end] = seg.segment;
                        if (time >= start && time < end) {
                            player.currentTime(end);
                            break;
                        }
                    }
                });
            };
        })


        return () => {
            cancelled = true;
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

                // Handle captions
                const selectedLanguages: string[] = JSON.parse(localStorage.getItem("langs") || "[]");
                const selected =  selectedLanguages.find(lang => video?.caption_langs.includes(lang));

                const captions = video?.caption_langs ? video?.caption_langs.map((code) => ({
                    kind: "captions",
                    src: `${videoBaseUrl}/sub.${code}.vtt`,
                    srclang: code,
                    label: INTL.of(code) || code,
                    default: code === selected
                })) : [];

                return <>
                    <h2>{video.title}</h2>
                    <VideoPlayer src = {`${videoBaseUrl}/video.mkv`} poster = {`${videoBaseUrl}/cover.webp`} id = {id} chapters = {video.chapters || []} captions = {captions} />
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
