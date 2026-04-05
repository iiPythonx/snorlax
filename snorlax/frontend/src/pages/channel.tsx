import { useEffect } from "preact/hooks";
import View from "../components/view";
import { useLocation } from "wouter";
import { useHeaderActions } from "../hooks/useHeaderActions";
import { usePageTitle } from "../hooks/usePageTitle";
import { useAsset } from "../hooks/useAsset";

export default function ChannelPage({ id }: { id: string }) {
    const { asset: channel, done } = useAsset(id, "channel");
    const { setActions } = useHeaderActions();
    const [, navigate] = useLocation();

    if (!channel) return done ? <p>
        Snorlax failed to make an API request for this page.
        <br />
        The channel might not exist, or there was a server issue.
    </p> : null;

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
    }, [id, channel]);

    usePageTitle(channel.name);

    return <>
        <section>
            <h2>{channel.name}</h2>
            <span style = {{ lineHeight: 2 }}>{channel.subscribers.toLocaleString()} subscribers</span>
        </section>
        <hr />
        <View endpoint = "videos" type = "video" params = {{ channel_id: channel.id }} />
    </>
}
