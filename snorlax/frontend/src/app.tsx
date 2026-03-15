import { Route, Switch } from "wouter";

import Home from "./pages/home.tsx";
import Watch from "./pages/watch.tsx";
import NotFound from "./pages/404.tsx";
import Search from "./pages/search.tsx";
import Channel from "./pages/channel.tsx";
import Manage from "./pages/manage.tsx";

export default function App() {
    return (
        <Switch>
            <Route path = "/" component = {Home} />
            <Route path = "/search" component = {Search} />
            <Route path = "/watch/:id">
                {params => <Watch id = {params.id} />}
            </Route>
            <Route path = "/channel/:id">
                {params => <Channel id = {params.id} />}
            </Route>
            <Route path = "/manage" component = {Manage} />
            <Route component = {NotFound} />
        </Switch>
    );
}
