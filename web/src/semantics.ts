import type { Mode, RecordChange } from "./types.ts";
export const symbols: Record<string, string> = {
  added: "+",
  removed: "−",
  modified: "↔",
  unchanged: "=",
  ambiguous: "?",
};
export function opacities(mode: Mode, mix: number): [number, number] {
  if (mode === "A") return [1, 0];
  if (mode === "B") return [0, 1];
  if (mode === "Compare") return [1 - mix, mix];
  return [0.28, 0.86];
}
export function visibleRecords(
  records: RecordChange[],
  changed: boolean,
  category: string,
  query: string,
) {
  return records.filter(
    (r) =>
      (!changed || r.status !== "unchanged") &&
      (category === "all" ||
        r.status === category ||
        r.changes.some((c) => c.category === category)) &&
      r.name.toLowerCase().includes(query.toLowerCase()),
  );
}
export function nextRecord(
  records: RecordChange[],
  id: string,
  direction: number,
) {
  if (!records.length) return null;
  const index = records.findIndex((r) => r.id === id);
  return records[(index + direction + records.length) % records.length].id;
}
export function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number(value.toFixed(5)).toString();
  if (Array.isArray(value)) return value.map(formatValue).join(" · ");
  if (typeof value === "object")
    return Object.entries(value)
      .map(([k, v]) => `${k.replaceAll("_", " ")}: ${formatValue(v)}`)
      .join("; ");
  return String(value);
}

/** Show only differing semantic subfields; retain full values in the JSON IR. */
export function valueRows(
  a: unknown,
  b: unknown,
  path = "",
): { path: string; before: unknown; after: unknown }[] {
  if (JSON.stringify(a) === JSON.stringify(b)) return [];
  if (a && b && typeof a === "object" && typeof b === "object") {
    const numericArrays =
      Array.isArray(a) &&
      Array.isArray(b) &&
      [...a, ...b].every((v) => typeof v === "number");
    if (!numericArrays) {
      const x = a as Record<string, unknown>,
        y = b as Record<string, unknown>;
      return [...new Set([...Object.keys(x), ...Object.keys(y)])].flatMap(
        (key) =>
          valueRows(
            x[key],
            y[key],
            [path, key.replaceAll("_", " ")].filter(Boolean).join(" / "),
          ),
      );
    }
  }
  return [{ path, before: a, after: b }];
}
