import { useState } from "preact/hooks";
import { Link } from "wouter";

export default function Header() {
    const [dropdownVisible, setDropdownVisible] = useState<boolean>(false);

    const toggleManageDropdown = () => {
        setDropdownVisible(!dropdownVisible);
    };

    return <>
        <section class = "flex snorlax-head">
            <h2>
                <img src = "/favicon.png" />
                <Link href = "/" class = "silent">Snorlax</Link>
            </h2>
            <Link href = "/search" class = "pad-left">Search</Link>
            <button onClick={toggleManageDropdown}>
                Manage ▾
                {dropdownVisible && (
                    <div className = "dropdown flex column">
                        <Link href = "/jobs">Jobs</Link>
                        <Link href = "/settings">Settings</Link>
                    </div>
                )}
            </button>
        </section>
        <hr />
    </>;
}