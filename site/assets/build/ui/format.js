export function text(value, fallback = "-") {
    if (value === undefined || value === null)
        return fallback;
    const result = String(value).trim();
    return result || fallback;
}
export function pick(...values) {
    for (const value of values) {
        const result = text(value, "");
        if (result)
            return result;
    }
    return "";
}
export function safeDate(value) {
    const raw = text(value, "");
    if (!raw)
        return null;
    const date = new Date(raw);
    return Number.isNaN(date.getTime()) ? null : date;
}
export function formatDate(value) {
    const date = safeDate(value);
    if (!date)
        return text(value);
    return new Intl.DateTimeFormat("nl-NL", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).format(date);
}
export function formatDateTime(value) {
    const date = safeDate(value);
    if (!date)
        return text(value);
    return new Intl.DateTimeFormat("nl-NL", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}
export function timestamp(value) {
    const date = safeDate(value);
    return date ? date.getTime() : 0;
}
export function formatBytes(value) {
    const bytes = Number(value);
    if (!Number.isFinite(bytes))
        return "-";
    if (bytes === 0)
        return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const size = bytes / Math.pow(1024, index);
    return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}
export function safeUrl(value) {
    const raw = text(value, "");
    if (!raw)
        return null;
    try {
        const parsed = new URL(raw, window.location.href);
        if (!["http:", "https:"].includes(parsed.protocol))
            return null;
        return parsed.href;
    }
    catch {
        return null;
    }
}
//# sourceMappingURL=format.js.map