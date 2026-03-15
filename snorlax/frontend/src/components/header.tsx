import { Link } from "wouter";

export default function Header() {
    return <>
        <section class = "flex snorlax-head">
            <h2>
                <img src = "/favicon.png" />
                <Link href = "/" class = "silent">Snorlax</Link>
            </h2>
            <Link href = "/search" class = "pad-left">Search</Link>
            <Link href = "/manage">Manage</Link>
        </section>
        <hr />
    </>;
}