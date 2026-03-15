const format = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
const secondAmounts: Partial<Record<Intl.RelativeTimeFormatUnit, number>> = {
    year:   60 * 60 * 24 * 365,
    month:  60 * 60 * 24 * 30,
    week:   60 * 60 * 24 * 7,
    day:    60 * 60 * 24,
    hour:   60 * 60,
    minute: 60,
    second: 1,
};

export function humanizeTime(timestamp: number): string {
    const now = Date.now() / 1000;
    const diff = now - timestamp;
    for (const unit of Object.keys(secondAmounts) as Intl.RelativeTimeFormatUnit[]) {
        const secondsInUnit = secondAmounts[unit] ?? 0;
        if (Math.abs(diff) >= secondsInUnit || unit === "second") return format.format(Math.round(-diff / secondsInUnit), unit);
    }

    return "forever ago";
}
