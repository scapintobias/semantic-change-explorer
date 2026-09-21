import test from "node:test";
import assert from "node:assert/strict";
import {
  opacities,
  visibleRecords,
  nextRecord,
  formatValue,
} from "./semantics.ts";
import type { RecordChange } from "./types.ts";
const records = [
  {
    id: "a",
    name: "Housing",
    status: "modified",
    changes: [{ category: "geometry" }],
  },
  { id: "b", name: "Panel", status: "unchanged", changes: [] },
  { id: "c", name: "Spacer", status: "ambiguous", changes: [] },
] as RecordChange[];
test("A and B endpoints are exact and crossfade never morphs geometry", () => {
  assert.deepEqual(opacities("A", 0.5), [1, 0]);
  assert.deepEqual(opacities("B", 0.5), [0, 1]);
  assert.deepEqual(opacities("Compare", 0), [1, 0]);
  assert.deepEqual(opacities("Compare", 1), [0, 1]);
});
test("filters preserve ambiguity", () =>
  assert.deepEqual(
    visibleRecords(records, true, "all", "").map((r) => r.id),
    ["a", "c"],
  ));
test("search and semantic category compose", () =>
  assert.equal(visibleRecords(records, false, "geometry", "house").length, 0));
test("navigation wraps and empty navigation is safe", () => {
  assert.equal(nextRecord(records, "c", 1), "a");
  assert.equal(nextRecord(records, "a", -1), "c");
  assert.equal(nextRecord([], "", 1), null);
});
test("values are text, including hostile names", () =>
  assert.equal(formatValue("<script>"), "<script>"));
import { valueRows } from "./semantics.ts";
test("inspector omits stable modifier fields and exposes edited width", () => {
  assert.deepEqual(
    valueRows(
      [{ name: "Bevel", settings: { width: 0.07, segments: 3 } }],
      [{ name: "Bevel", settings: { width: 0.18, segments: 3 } }],
    ),
    [{ path: "0 / settings / width", before: 0.07, after: 0.18 }],
  );
});
