import { humanizeTime } from "./humanize.js";

const VIDEO_ID = window.location.pathname.split("/")[2];
const MAIN_ELEMENT = document.querySelector("main");

// Fetch video data
const response = await (await fetch(`/v1/video/${VIDEO_ID}`)).json();
if (response.code !== 200) {
    MAIN_ELEMENT.innerHTML = "<p>404: Not Found</p><a href = '/'>Click here to head back to the homepage.</a>";
} else {
    const video = response.data;
    const channel = (await (await fetch(`/v1/channel/${video.channel_id}`)).json()).data;

    // Description
    let description = video.description.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    description = description.replace(/(https?:\/\/[^\s]+)/g, `<a href = "$1" target = "_blank" rel = "noopener noreferrer">$1</a>`);

    // Render HTML
    const url = `/videos/${video.channel_id}/${video.id}`;
    MAIN_ELEMENT.innerHTML = `
        <section>
            <h2><a href = "/">Snorlax</a></h2>
        </section>
        <hr>
        <h2>${video.title}</h2>
        <video-js controls preload = "auto" poster = "${url}/cover.webp" data-setup = "{}" class = "vjs-fluid">
            <source src = "${url}/video.mkv" type = "video/matroska">
        </video-js>
        <hr>
        <span>
            <a href = "/channel/${channel.id}">${channel.name}</a> (${channel.subscribers.toLocaleString()} subscribers) <br>
            ${video.duration_string} • ${video.view_count.toLocaleString()} views • ${video.like_count.toLocaleString()} likes • ${humanizeTime(video.timestamp)}
        </span>
        <hr>
        <pre style = "margin-bottom: 20px;">${description}</pre>
    `;
    const video_element = document.querySelector("video-js");

    // Handle captions
    const languages = new Intl.DisplayNames(["en"], { type: "language" });
    if (video.caption_langs) {
        for (const lang of video.caption_langs.split(",")) {
            const track = document.createElement("track");
            track.kind = "captions"
            track.src = `${url}/sub.${lang}.vtt`;
            track.srclang = lang;
            track.label = languages.of(lang) || lang;
            track.default = ["en", "en-GB"].includes(lang);
            video_element.appendChild(track);
        }
    }

    // Initialize playback
    videojs(video_element);
}
