// Copyright (c) 2026 iiPython

import { humanizeTime } from "./lib/humanize.js";

{
    for (const list of document.querySelectorAll("[data-api-type]")) {
        const settings = {
            type:     list.getAttribute("data-api-type"),      // 'video' or 'channel'
            endpoint: list.getAttribute("data-api-endpoint"),  // ex. /v1/videos
            limit:   +list.getAttribute("data-api-limit"),     // amount of items to return
            params:   list.getAttribute("data-api-params")     // channel_id=420, query=resident%20evil, etc.
        };

        let page = 1, total = 1;
        
        // Make request
        const container = list.querySelector("div");
        async function load() {
            if (settings.endpoint === "search" && !settings.params) {
                container.innerHTML = `<span>Nothing to show.</span>`;
                return;
            }

            const query = settings.params.split(",").map(p => {
                const [k, v] = p.split("=");
                return `${encodeURIComponent(k)}=${encodeURIComponent(v ?? "")}`;
            }).join("&");

            const response = await (await fetch(`/v1/${settings.endpoint}?page=${page}&limit=${settings.limit}${query && '&'}${query}`)).json();
            total = Math.ceil(response.data.total / settings.limit);
    
            // Build page
            container.innerHTML = !response.data.items.length ? "<span>No results returned from API.</span>" : "";
            for (const item of response.data.items) {
                const element = document.createElement("article");
                switch (settings.type) {
                    case "video":
                        element.innerHTML = `
                            <a href = "/watch/${item.id}" class = "video-poster flex column">
                                <img src = "/videos/${item.channel_id}/${item.id}/cover.webp">
                                <span class = "duration-string">${item.duration_string}</span>
                                <span>${item.title}</span>
                            </a>
                            <div>
                                <a href = "/channel/${item.channel_preferred_id}" class = "silent">${item.channel_name}</a> <br>
                                <span>${item.view_count.toLocaleString()} views • ${humanizeTime(item.timestamp)}</span>
                            </div>
                        `;
                        break;
    
                    case "channel":
                        element.innerHTML = `<a href = "/channel/${item.preferred_id}">${item.name}</a>`;
                        break;
                }
    
                // Add to the pile
                container.appendChild(element);
            }
        }
    
        // Handle interface
        const load_time = list.querySelector(".api-time")
        const indicator = list.querySelector(".current-page");
        const btn_back = list.querySelector(".btn-back"), btn_next = list.querySelector(".btn-next");

        async function update() {
            const start = Date.now();
            await load();

            load_time.innerText = `[ ${(Date.now() - start)}ms ]`;
            indicator.innerText = `| Page ${page} / ${total} |`;

            btn_back.disabled = page === 1;
            btn_next.disabled = page === total;
        }
    
        update();

        // Handle buttons
        btn_back.addEventListener("click", () => {
            if (page > 1) { page--; update(); };
        });
        btn_next.addEventListener("click", () => {
            if (page + 1 <= total) { page++; update(); }
        });

        // Allow settings updates
        list.snorlaxUpdateParams = (params) => {
            settings.params = params, page = 1;
            update();
        };
    }
}

