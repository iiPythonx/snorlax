import path from "path";

import { defineConfig } from "vite";
import preact from "@preact/preset-vite";

import { version } from "../../package.json" with { type: "json" };

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
