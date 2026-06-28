export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function parseJsonl<T extends Record<string, unknown>>(sourceText: string, source = "JSONL"): T[] {
  const records: T[] = [];
  const lines = String(sourceText || "").split(/\r?\n/);
  for (const [index, rawLine] of lines.entries()) {
    const line = rawLine.trim();
    if (!line) continue;
    try {
      const parsed: unknown = JSON.parse(line);
      if (isPlainObject(parsed)) {
        records.push(parsed as T);
      } else {
        console.warn(`${source}: regel ${index + 1} is geen object en wordt overgeslagen.`);
      }
    } catch (error) {
      console.warn(`${source}: regel ${index + 1} bevat ongeldige JSON en wordt overgeslagen.`, error);
    }
  }
  return records;
}

export async function loadJson<T extends Record<string, unknown>>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`Kan ${path} niet laden, status ${response.status}`);
  const parsed: unknown = await response.json();
  if (!isPlainObject(parsed)) throw new Error(`${path} bevat geen JSON-object.`);
  return parsed as T;
}

export async function loadOptionalJson<T extends Record<string, unknown>>(path: string): Promise<T | null> {
  try {
    return await loadJson<T>(path);
  } catch (error) {
    console.warn(`Optionele JSON-export kon niet worden geladen: ${path}`, error);
    return null;
  }
}

export async function loadJsonl<T extends Record<string, unknown>>(path: string): Promise<T[]> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`Kan ${path} niet laden, status ${response.status}`);
  return parseJsonl<T>(await response.text(), path);
}

export async function loadOptionalJsonl<T extends Record<string, unknown>>(path: string): Promise<T[]> {
  try {
    return await loadJsonl<T>(path);
  } catch (error) {
    console.warn(`Optionele export kon niet worden geladen: ${path}`, error);
    return [];
  }
}
