import { Elysia } from "elysia";
import { SnorlaxDB } from ".";

const db = new SnorlaxDB();

export const dbPlugin = new Elysia({ name: "db" })
    .decorate("db", db);
