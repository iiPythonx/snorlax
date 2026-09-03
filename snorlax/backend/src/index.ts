import { Elysia, t } from "elysia";
import { SnorlaxDB } from "./database/index.js";
import { apiRoutes } from "./routes/api.js";

// Initialize database
const db = new SnorlaxDB();

function exit() {
    db.close()
    process.exit(0);
}

process.on("SIGINT",  exit);
process.on("SIGTERM", exit);

// Setup Elysia
const app = new Elysia()
    .decorate("db", db)
    .use(apiRoutes)
    .listen(3000);

console.log(`🦊 Elysia server running at ${app.server?.hostname}:${app.server?.port}`);
