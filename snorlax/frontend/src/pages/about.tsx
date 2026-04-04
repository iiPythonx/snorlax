export default function About() {
    return <>
        <span>You are running Snorlax v{__VERSION__}, built by <a href = "https://iipython.dev">iiPython</a>.</span>
        <span>
            Made possible by <a href = "https://fastapi.tiangolo.com/">FastAPI</a>,{" "}
            <a href = "https://github.com/yt-dlp/yt-dlp">yt-dlp</a>,{" "}
            <a href = "https://vite.dev">vite</a>,{" "}
            <a href = "https://preactjs.com">preact</a>,
            and <a href = "https://videojs.org">video.js</a>,
            among many others.
        </span>
        <span>The source is available on <a href = "https://github.com/iiPythonx/snorlax">GitHub</a>, and issues can be reported <a href = "https://github.com/iiPythonx/snorlax/issues">here</a>.</span>
    </>;
}
