import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import path from "path";
import toml from "toml";
import fs from "fs";

const pyproject = toml.parse(fs.readFileSync("../../pyproject.toml", "utf-8"));
const version = pyproject?.project?.version || "N/A";

export default defineConfig({
    root: path.resolve(import.meta.dirname),
    plugins: [preact()],
    server: {
        proxy: {
            "/v1": "http://localhost:3000"
        }
    },
    build: {
        chunkSizeWarningLimit: 750,  // To silence the Video.js chunk warning
    },
    define: {
        __VERSION__: JSON.stringify(version)
    }
});
