import { humanizeTime } from "./humanize.js";

const VIDEO_ID = window.location.pathname.split("/")[2];
const MAIN_ELEMENT = document.querySelector("main");

// Fetch video data
const response = await (await fetch(`/v1/video/${VIDEO_ID}`)).json();
if (response.code !== 200) {
    MAIN_ELEMENT.innerHTML = "<p>404: Not Found</p><a href = '/'>Click here to head back to the homepage.</a>";
} else {
    const video = response.data;
    const channel = (await (await fetch(`/v1/channel/${video.uploader_id}`)).json()).data;

    // Render HTML
    const url = `/videos/${video.uploader_id}/${video.id}`;
    MAIN_ELEMENT.innerHTML = `
        <h2>${video.title}</h2>
        <hr>

        <!-- Video -->
        <video-js controls preload = "auto" poster = "${url}/cover.webp" data-setup = "{}" class = "vjs-fluid">
            <source src = "${url}/video.webm" type = "video/webm">
        </video-js>

        <hr>
        <span>
            <a href = "/channel/${channel.id}">${channel.name}</a> (${channel.subscribers.toLocaleString()} subscribers) <br>
            ${video.duration_string} • ${video.view_count.toLocaleString()} views • ${video.like_count.toLocaleString()} likes • ${humanizeTime(video.timestamp)}
        </span>
        <hr>
        <pre style = "margin-bottom: 20px;">${video.description}</pre>
    `;
    const video_element = document.querySelector("video-js");

    // Handle captions
    const languages = new Intl.DisplayNames(["en"], { type: "language" });
    for (const lang of video.caption_langs.split(",")) {
        const track = document.createElement("track");
        track.kind = "captions"
        track.src = `${url}/sub.${lang}.vtt`;
        track.srclang = lang;
        track.label = languages.of(lang) || lang;
        track.default = ["en", "en-GB"].includes(lang);
        video_element.appendChild(track);
    }

    // Initialize playback
    videojs(video_element);
}
