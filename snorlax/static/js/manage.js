import { humanizeTime } from "./humanize.js";

// Handle job listing
const ws = new WebSocket("/v1/jobs");
const joblist = document.getElementById("job-list");

ws.addEventListener("message", (e) => {
    joblist.innerHTML = "";
    for (const [id, data] of Object.entries(JSON.parse(e.data))) {
        if (!data.status) continue;
        const finished = ["finished", "failed"].includes(data.status);

        // Progress calculation
        const completed_amount = Math.round(20 * (data.progress / 100));
        const progress_spacing = 20 - completed_amount;

        // Build HTML
        const element = document.createElement("article");
        element.innerHTML = `
            <div class = "flex">
                <a href = "/watch/${id}">${data.title}</a>
                ${finished ? '<button class = "pad-left">Remove Job</button>' : ''}
            </div>
            <div class = "flex">
                ${data.status === "failed" ? "failed, check server console for details" : `
                    <a href = "/channel/${data.channel_id}">${data.channel}</a> •
                    ${humanizeTime(data.timestamp)} • ${data.status} ${data.status === 'downloading' ? `• ${data.speed} MiB/s • ETA ${data.eta}s` : ''}
                `}
                <pre class = "pad-left">[${'='.repeat(completed_amount)}${' '.repeat(progress_spacing)}] ${data.progress}%</pre>
            </div>
            <br> <hr>
        `;
        joblist.appendChild(element);

        // Job removal
        if (finished) element.querySelector("button").addEventListener("click", () => {
            ws.send(JSON.stringify({ type: "remove-job", id }));
            element.remove();
        });
    }
});

// Handle adding jobs
const regex = { video: /(?:\.be\/|\?v=)([\w-]+)/, channel: /(?:\/@|l\/)([\w-]+)/ };
document.getElementById("btn-add-job").addEventListener("click", () => {
    const url = prompt("Target URL (video/channel url)");
    if (!url) return;

    // Extract ID
    let type = null, id = null;
    for (const [key, pattern] of Object.entries(regex)) {
        const match = url.match(pattern);
        if (match) {
            type = key, id = match[1];
            break;
        }
    }
    if (!type) return alert("URL could not be processed.");

    // Send off job
    ws.send(JSON.stringify({ type: `add-${type}-job`, id: type === "channel" ? `@${id}` : id }));
});
