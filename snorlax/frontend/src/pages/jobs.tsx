import Paginator from "../components/paginator";

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

export default function Jobs() {

    // Handle adding job
    const addJob = async () => {
        const url = prompt("Target URL (video/channel url)");
        if (url) await fetch(`/v1/jobs/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
    }

    // Handle canceling job
    const cancelJob = (id: string) => {
        console.log("delete job", id);
    }

    return <>
        <section className = "flex column">
            <div className = "flex">
                <h2>Current Jobs</h2>
                <button className = "pad-left" id = "btn-add-job" onClick = {addJob}>Add Job</button>
            </div>
        </section>
        <hr />
        <section>
            <div className = "flex column" id = "job-list">
                <Paginator type = "job" endpoint = "jobs" />
            </div>
        </section>
    </>;
}