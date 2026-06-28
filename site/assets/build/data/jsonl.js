export function isPlainObject(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
export function parseJsonl(sourceText, source = "JSONL") {
    const records = [];
    const lines = String(sourceText || "").split(/\r?\n/);
    for (const [index, rawLine] of lines.entries()) {
        const line = rawLine.trim();
        if (!line)
            continue;
        try {
            const parsed = JSON.parse(line);
            if (isPlainObject(parsed)) {
                records.push(parsed);
            }
            else {
                console.warn(`${source}: regel ${index + 1} is geen object en wordt overgeslagen.`);
            }
        }
        catch (error) {
            console.warn(`${source}: regel ${index + 1} bevat ongeldige JSON en wordt overgeslagen.`, error);
        }
    }
    return records;
}
export async function loadJson(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok)
        throw new Error(`Kan ${path} niet laden, status ${response.status}`);
    const parsed = await response.json();
    if (!isPlainObject(parsed))
        throw new Error(`${path} bevat geen JSON-object.`);
    return parsed;
}
export async function loadOptionalJson(path) {
    try {
        return await loadJson(path);
    }
    catch (error) {
        console.warn(`Optionele JSON-export kon niet worden geladen: ${path}`, error);
        return null;
    }
}
export async function loadJsonl(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok)
        throw new Error(`Kan ${path} niet laden, status ${response.status}`);
    return parseJsonl(await response.text(), path);
}
export async function loadOptionalJsonl(path) {
    try {
        return await loadJsonl(path);
    }
    catch (error) {
        console.warn(`Optionele export kon niet worden geladen: ${path}`, error);
        return [];
    }
}
//# sourceMappingURL=jsonl.js.map