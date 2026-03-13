{
    let timeout;
    document.querySelector("input").addEventListener("keydown", (e) => {
        if (timeout) clearTimeout(timeout);
        timeout = setTimeout(() => {
            document.querySelector("div[data-api-type]").snorlaxUpdateParams(`query=${e.target.value}`);
        }, 500);
    });
}
