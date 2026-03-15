import Header from "../components/header";
import Paginator from "../components/paginator";
import { useChannel } from "../hooks/useChannel";

export default function ChannelPage({ id }: { id: string }) {
    const { channel, errored } = useChannel(id);
    if (errored) return <p>
        Snorlax failed to make an API request for this page.
        <br />
        The channel might not exist, or there was a server issue.
    </p>;    

    return <>
        <Header />
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
