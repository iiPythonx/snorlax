import Header from "../components/header";
import Paginator from "../components/paginator";

export default function Home() {
    return <>
        <Header />
        <h2>Channels</h2>
        <Paginator type = "channel" endpoint = "channels" limit = {16} />
        <h2>Videos</h2>
        <Paginator type = "video" endpoint = "videos" />
    </>;
}