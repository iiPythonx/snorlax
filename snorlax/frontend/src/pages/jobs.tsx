import { useRef } from "preact/hooks";
import View from "../components/view";
import type { ViewHandle } from "../components/view";
import type { Job } from "../types/api";

export default function Jobs() {
    const viewRef = useRef<ViewHandle>(null);

    const addJob = async () => {
        const url = prompt("Target URL (video/channel url)");
        if (url) await fetch(`/v1/jobs/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
    }

    const cancelJob = async (job: Job) => {
        await fetch(`/v1/jobs/${job.job_id}`, { method: "DELETE" });
        viewRef.current?.refresh();
    }

    return <>
        <section className = "flex column">
            <div className = "flex" style = {{ alignItems: "center" }}>
                <h2>Current Jobs</h2>
                <button className = "pad-left" onClick = {() => viewRef.current?.refresh()}>Refresh</button>
                {"|"}
                <button onClick = {addJob}>Add Job</button>
            </div>
        </section>
        <hr />
        <View type = "job" endpoint = "jobs" refreshTime = {10} onJobCancel = {cancelJob} ref = {viewRef} />
    </>;
}