import { Elysia } from "elysia";
import { SnorlaxDB } from "./database/index.js";

// Initialize database
const db = new SnorlaxDB();

function exit() {
    db.close()
    process.exit(0);
}

process.on("SIGINT",  exit);
process.on("SIGTERM", exit);

// Setup Elysia
const app = new Elysia().get("/", () => "Hello Elysia").listen(3000);
console.log(`🦊 Elysia is running at ${app.server?.hostname}:${app.server?.port}`);
