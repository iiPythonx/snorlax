import View from "../components/view";

export default function Home() {
    return <>
        <h2>Channels</h2>
        <View type = "channel" endpoint = "channels" limit = {16} />
        <h2>Videos</h2>
        <View type = "video" endpoint = "videos" />
    </>;
}