const format = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
const secondAmounts = {
    year:   60 * 60 * 24 * 365,
    month:  60 * 60 * 24 * 30,
    week:   60 * 60 * 24 * 7,
    day:    60 * 60 * 24,
    hour:   60 * 60,
    minute: 60,
    second: 1,
};

export function humanizeTime(timestamp) {
    const now = Date.now() / 1000;
    const diff = now - timestamp;
    for (const [unit, secondsInUnit] of Object.entries(secondAmounts)) {
        if (Math.abs(diff) >= secondsInUnit || unit === "second") return format.format(Math.round(-diff / secondsInUnit), unit);
    }
}