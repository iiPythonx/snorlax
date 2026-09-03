// Copyright (c) 2026 iiPython

import SQL from "./tables.sql" with { type: "text" };
import { Database } from "bun:sqlite";

export class SnorlaxDB {
    private db: Database;

    constructor() {
        this.db = new Database("snorlax.db");
        this.init();
    }

    close() {
        this.db.run("PRAGMA wal_checkpoint(TRUNCATE);");
        this.db.close();
    }

    async init() {
        this.db.run(SQL);
    }
}