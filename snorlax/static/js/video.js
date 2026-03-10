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
    console.log(video, channel);

    // Render HTML
    const url = `/videos/${video.uploader_id}/${video.id}`;
    MAIN_ELEMENT.innerHTML = `
        <h2>${video.title}</h2>
        <hr>

        <!-- Video -->
        <video-js controls preload = "auto" poster = "${url}.webp" data-setup = "{}" class = "vjs-fluid">
            <source src = "${url}.webm" type = "video/webm">
            <track kind = "captions" src = "${url}.en.vtt" srclang = "en" label = "English" default>
        </video-js>

        <hr>
        <span>
            <a href = "/channel/${channel.id}">${channel.name}</a> (${channel.subscribers.toLocaleString()} subscribers) <br>
            ${video.duration_string} • ${video.view_count.toLocaleString()} views • ${video.like_count.toLocaleString()} likes • ${humanizeTime(video.timestamp)}
        </span>
        <hr>
        <pre style = "margin-bottom: 20px;">${video.description}</pre>
    `;

    videojs(document.querySelector("video-js"));
}
