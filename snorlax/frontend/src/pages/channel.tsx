import { useEffect } from "preact/hooks";
import Paginator from "../components/paginator";
import { useChannel } from "../hooks/useChannel";
import { useLocation } from "wouter";
import { useHeaderActions } from "../hooks/useHeaderActions";

export default function ChannelPage({ id }: { id: string }) {
    const { channel, errored } = useChannel(id);
    const { setActions } = useHeaderActions();
    const [, navigate] = useLocation();

    if (errored) return <p>
        Snorlax failed to make an API request for this page.
        <br />
        The channel might not exist, or there was a server issue.
    </p>;

    useEffect(() => {
        setActions([
            {
                label: "Remove Channel",
                onClick: async () => {
                    const sure = confirm("Are you sure you want to delete this channel? This will delete ALL of its videos as well.");
                    if (sure !== true) return;

                    await fetch(`/v1/channel/${id}`, { method: "DELETE" });
                    navigate("/");
                },
            },
        ]);
        return () => setActions([]);
    }, [id]);

    return <>
        {channel && <>
            <section>
                <h2>{channel.name}</h2>
                <span style = {{ lineHeight: 2 }}>{channel.subscribers.toLocaleString()} subscribers</span>
            </section>
            <hr />
            <Paginator endpoint = "videos" type = "video" params = {{ channel_id: channel.id }} />
        </>}
    </>;
}
