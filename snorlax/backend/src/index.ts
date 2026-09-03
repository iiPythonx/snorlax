// Copyright (c) 2026 iiPython

import { mkdirSync } from "node:fs";

import { Elysia } from "elysia";
import staticPlugin from "@elysiajs/static";

import { SnorlaxDB } from "./database/index.js";
import { apiRoutes } from "./routes/api.js";
import { dbPlugin } from "./database/elysia.js";
import { config } from "./config.js";

// Initialize database
const db = new SnorlaxDB();

function exit() {
    db.close()
    process.exit(0);
}

process.on("SIGINT",  exit);
process.on("SIGTERM", exit);

// Make sure video path exists
const video_path = config.snorlax.video_path;
mkdirSync(video_path, { recursive: true });

// Setup Elysia
const app = new Elysia()
    .use(
        staticPlugin({
            prefix: "/v1/assets",
            assets: video_path
        })
    )
    .use(dbPlugin)
    .use(apiRoutes)
    .listen(3000);

console.log(`Zz (￣▵—▵￣) zZ\nSnorlax backend running at http://${app.server?.hostname}:${app.server?.port}/`);
