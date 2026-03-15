import { Link } from "wouter";

export default function NotFound() {
    return <>
        <p>404: Not Found</p>
        <Link href = "/">Click here to head back to the homepage.</Link>
    </>;
}
