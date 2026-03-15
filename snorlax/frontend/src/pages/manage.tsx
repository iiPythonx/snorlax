import { useEffect, useRef, useState } from "preact/hooks";
import Header from "../components/header";
import { Link } from "wouter";
import { humanizeTime } from "../lib/time";

type Job = {
    title:                string;
    channel:              string;
    channel_preferred_id: string;
    timestamp:            number;
    status:               string;
    progress:             number;
    speed?:               number;
    eta?:                 number;
};

type JobMap = Record<string, Job>

export default function Manage() {
    const [jobs, setJobs] = useState<JobMap>({});
    const socketReference = useRef<WebSocket | null>(null);

    // Connect to websocket
    useEffect(() => {
        const ws = new WebSocket("/v1/jobs");
        ws.addEventListener("message", (e) => setJobs(JSON.parse(e.data) as JobMap));
        
        socketReference.current = ws;

        return () => ws.close();
    }, []);

    // Handle adding job
    const addJob = () => {
        const url = prompt("Target URL (video/channel url)");
        if (!url) return;

        const regex: Record<string, RegExp> = {
            video:   /(?:\.be\/|\?v=)([\w-]+)/,
            channel: /(?:\/@|l\/)([\w-]+)/
        };

        let type: "video" | "channel" | null = null;
        let id: string | null = null;

        for (const [key, pattern] of Object.entries(regex)) {
            const match = url.match(pattern);
            if (match) {
                type = key as "video" | "channel";
                id = match[1];
                break;
            }
        }
        if (!(type && id)) return alert("URL could not be processed.");

        // Send off job
        socketReference.current?.send(JSON.stringify({ type: `add-${type}-job`, id: type === "channel" ? `@${id}` : id }));
    }

    // Handle canceling job
    const cancelJob = (id: string) => {
        socketReference.current?.send(JSON.stringify({ type: "cancel-job", id }));
        setJobs((prev) => {
            const { [id]: _, ...rest } = prev;
            return rest;
        });
    }

    return <>
        <Header />
        <section className = "flex column">
            <div className = "flex">
                <h2>Current Jobs</h2>
                <button className = "pad-left" id = "btn-add-job" onClick = {addJob}>Add Job</button>
            </div>
        </section>
        <hr />
        <section>
            <div className = "flex column" id = "job-list">
                {Object.entries(jobs).filter(([_, job]) => job.status).map(([id, job]) => {
                    const finished = ["finished", "failed"].includes(job.status);

                    // Progress calculation
                    const completed_amount = Math.round(20 * (job.progress / 100));
                    const progress_spacing = 20 - completed_amount;

                    return (
                        <article>
                            <div className = "flex">
                                <Link href = {`/watch/${id}`}>{job.title || id}</Link>
                                <button className = "pad-left" onClick = {() => cancelJob(id)}>{finished ? "Remove" : "Cancel"} Job</button>
                            </div>
                            <div className = "flex">
                                <Link href = {`/channel/${job.channel_preferred_id}`}>{job.channel || 'N/A'}</Link> •
                                {" "}{job.timestamp ? humanizeTime(job.timestamp) : 'N/A'} • {job.status} {job.status === "downloading" && `• ${job.speed} MiB/s • ETA ${job.eta}s`}
                                <pre className = "pad-left">[{"=".repeat(completed_amount)}{" ".repeat(progress_spacing)}] <span style = {{ width: "30px", display: "inline-block", textAlign: "right" }}>{job.progress}%</span></pre>
                            </div>
                            <br />
                            <hr />
                        </article>
                    )
                })}
            </div>
        </section>
    </>;
}