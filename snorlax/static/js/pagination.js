// Copyright (c) 2026 iiPython

import { humanizeTime } from "./humanize.js";

{
    for (const list of document.querySelectorAll("[data-api-type]")) {
        const type = list.getAttribute("data-api-type");
        const limit = +list.getAttribute("data-api-limit");
        const filters = list.getAttribute("data-api-filter");
        
        let page = 1, total = 10e10;
        
        // Make request
        const container = list.querySelector("div");
        async function load() {
            const response = await (await fetch(`/v1/${type}s?page=${page}&limit=${limit}${filters && '&'}${filters}`)).json();
            total = Math.ceil(response.data.total / limit);
    
            // Build page
            container.innerHTML = "";
            for (const item of response.data.items) {
                const element = document.createElement("article");
                switch (type) {
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
                        element.innerHTML = `<a href = "/channel/${item.handle || item.id}">${item.name}</a>`;
                        break;
                }
    
                // Add to the pile
                container.appendChild(element);
            }
        }
    
        // Handle interface
        const indicator = list.querySelector("& > article span");
        const btn_back = list.querySelector(".btn-back"), btn_next = list.querySelector(".btn-next");

        async function update() {
            await load();
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
    }
}

