import { useState } from "preact/hooks";
import { Link } from "wouter";
import { useHeaderActions } from "../hooks/useHeaderActions";

export default function Header() {
    const { actions } = useHeaderActions();
    const [dropdownVisible, setDropdownVisible] = useState<boolean>(false);

    const toggleManageDropdown = () => setDropdownVisible(v => !v);

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
                        <Link href = "/about">About</Link>
                        {actions.length > 0 && (
                            <>
                                <hr />
                                {actions.map(action => <button onClick = {action.onClick}>{action.label}</button>)}
                            </>
                        )}
                    </div>
                )}
            </button>
        </section>
        <hr />
    </>;
}