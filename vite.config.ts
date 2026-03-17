import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import path from "path";

export default defineConfig({
    root: path.resolve(__dirname, "snorlax", "frontend"),
    plugins: [preact()],
    server: {
        proxy: {
            "/v1": "http://localhost:8000"
        }
    },
    build: {
        chunkSizeWarningLimit: 700,  // To silence the Video.js chunk warning
    }
});
