import { Route, Switch } from "wouter";
import { useState } from "preact/hooks";
import { lazy, Suspense } from "preact/compat";

import { HeaderActionContext } from "./hooks/useHeaderActions";
import type { HeaderAction } from "./types/header";

import Home from "./pages/home.tsx";
import NotFound from "./pages/404.tsx";
import Search from "./pages/search.tsx";
import Channel from "./pages/channel.tsx";
import Jobs from "./pages/jobs.tsx";
import Settings from "./pages/settings.tsx";
import Header from "./components/header.tsx";

const Watch = lazy(() => import("./pages/watch.tsx"));

export default function App() {
    const [actions, setActions] = useState<HeaderAction[]>([]);
    return (
        <HeaderActionContext.Provider value={{ actions, setActions }}>
            <Header />
            <Switch>
                <Route path = "/" component = {Home} />
                <Route path = "/search" component = {Search} />
                <Route path = "/watch/:id">
                    {params => <Suspense fallback = {null}><Watch id = {params.id} /></Suspense>}
                </Route>
                <Route path = "/channel/:id">
                    {params => <Channel id = {params.id} />}
                </Route>
                <Route path = "/jobs" component = {Jobs} />
                <Route path = "/settings" component = {Settings} />
                <Route component = {NotFound} />
            </Switch>
        </HeaderActionContext.Provider>
    );
}
