// Copyright (c) 2026 iiPython

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
                            <a href = "/watch/${item.id}">
                                <img src = "/videos/${item.uploader_id}/${item.id}.webp">
                                <span>${item.title}</span>
                            </a>
                            <span>${item.duration_string} • ${item.view_count} views • ${item.timestamp}</span>
                        `;
                        break;
    
                    case "channel":
                        element.innerHTML = `<a href = "/channel/${item.id}">${item.name}</a>`;
                        break;
                }
    
                // Add to the pile
                container.appendChild(element);
            }
        }
    
        // Handle interface
        const indicator = list.querySelector("& > article span");
        async function update() {
            await load();
            indicator.innerText = `| Page ${page} / ${total} |`;
        }
    
        update();

        // Handle buttons
        list.querySelector(".btn-back").addEventListener("click", () => {
            if (page > 1) { page--; update(); };
        });
        list.querySelector(".btn-next").addEventListener("click", () => {
            if (page + 1 <= total) { page++; update(); }
        });
    }
}

