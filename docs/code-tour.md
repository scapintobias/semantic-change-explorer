# Code tour: follow one comparison

Start with [product thesis](product-thesis.md) and [data model](data-model.md). Then keep the canonical report and these files open together. All source paths below are repository-relative.

## 1. Command to operation
`src/semantic_change_explorer/cli.py`: `main`, `run`.

Input: `sce compare before.blend after.blend --output report`. Output: a completed directory and summary, or exit code 2 with an actionable message. `main` parses four purposeful commands; `run` refuses existing outputs and creates staging space. Example: a typo in Blender's path fails before a report is presented as complete. Debug mode preserves the traceback for diagnosis.

## 2. Cross the process boundary
`src/semantic_change_explorer/adapters/blender.py`: `locate`, `extract`.

Input: source path, output paths and optional executable. Output: validated snapshot plus timings. `locate` verifies a parseable version and accepts Blender 4.2–4.5; acceptance is not the same as all versions tested. `extract` hashes input bytes, invokes Blender with an argument array and a timeout, and rehashes on return. The autoexec flag precedes the file argument. Example: a filename containing spaces or shell metacharacters is one argument, not executable shell text.

## 3. Observe Blender
`src/semantic_change_explorer/adapters/blender_extract.py`: `main`, `mesh_info`, `clean`, `digest`.

Input: Blender's loaded scene and command-line output paths. Output: canonical snapshot JSON, optionally GLB, and a timing line. `mesh_info` observes vertex indices and local positions; it cannot solve arbitrary shape equivalence. `main` reads original datablocks first, then dependency-graph evaluated meshes. Example: increasing Bevel width leaves `mesh` unchanged but changes `evaluated`. Temporary evaluated meshes are cleared after extraction.

The snapshot is written before adding preview metadata. Evaluated meshes are copied into new temporary objects, assigned `sce_entity`, selected and exported through Blender's glTF exporter. No save operator exists in this production script. Compare it with the trusted fixture generator, whose explicit purpose is to save new demo files.

## 4. Read canonical observations
`src/semantic_change_explorer/core/model.py`: `canonical`, `dumps`, `validate`, `read`, `equivalent`.

Input: JSON-compatible observations. Output: stable JSON or validated snapshot. Six-decimal rounding is the serialization policy; 1e-5 absolute tolerance is the comparison policy. Example: `-0.0` serializes as `0.0`; a position difference of 0.000009 is ignored. Key sorting does not reorder meaningful sequences such as modifier stacks. Validation rejects duplicate IDs and dangling relationship references.

## 5. Decide what may correspond
`src/semantic_change_explorer/core/matching.py`: `evidence`, `match`.

Input: two snapshots. Output: accepted pairs and unresolved candidate edges. A unique high-ranked match must be preferred from both directions by a margin. Example: Body → Housing with identical geometry/context is a probable rename; two equal candidates remain ambiguous. Scores are ordinal ranking weights, not probabilities. No historical identity is recovered from local ordinal IDs.

## 6. Explain differences
`src/semantic_change_explorer/core/diff.py`: `compare`.

Input: validated snapshots plus optional effects callback. Output: Change IR and host timings. It intersects coverage, compares typed properties, translates old relationship references through correspondence, adds/removes only unresolved-free observations, and preserves ambiguity separately. Example: renaming a parent does not itself create a child reparenting change.

`src/semantic_change_explorer/adapters/blender.py`: `effects` is the Blender-specific callback. Input: matched entities and common coverage. Output: geometry/evaluated change records. Compatible topology uses index-wise Euclidean displacement; incompatible topology returns counts/bounds and an explicit compatibility flag. Example: moving a local vertex yields changed count/max/mean; moving the whole object does not change mesh-local positions.

## 7. Make the report portable
`src/semantic_change_explorer/report.py`: `viewer_assets`, `build_report`, `serve`, `LocalHandler`.

Input: both snapshots, IR, GLBs and timings. Output: static files served on loopback. Viewer assets come from the packaged wheel or local Vite build. Data is JSON, not interpolated HTML. Example: an object named `<script>` remains text in React. `serve` checks required assets and constrains file access to the selected root.

## 8. Load the browser model
`web/src/main.tsx`: `App` and the `fetch` startup.

Input: `report.json`. Output: a DOM index/inspector and props for the viewport. React owns selected record, filters, mode, mix and fit/reset requests. Example: clicking Lower housing sets its record ID, causing the inspector and viewport to update together. Unknown schema or missing JSON shows an error instead of a blank dashboard.

`web/src/semantics.ts`: `visibleRecords`, `nextRecord`, `opacities`, `formatValue` keep small behavior deterministic and independently testable. Example: Compare at zero displays only A; at one only B.

## 9. Turn a visual hit into a semantic selection
`web/src/Viewer.tsx`: `Viewer`, its setup effect, local `fit`, `pointerUp`, and appearance effect.

Input: React state and report. Output: a Three.js scene. `GLTFLoader` loads A/B; each mesh inherits its owning exported `sce_entity`. That snapshot ID maps to a Change IR record. Raycasting finds a mesh, retrieves the record ID and calls React's `onSelect`. Reverse direction: selected record ID highlights its A/B meshes and provides bounds for fitting.

One shared perspective camera and OrbitControls avoid synchronization races. Renderer, geometry, cloned materials, controls and resize observer are disposed on unmount. Scene updates render on demand. An earlier browser test caught an important Three.js contract: single-material geometry must retain a single material; converting it to an array without geometry groups makes it invisible. The current implementation preserves that shape.

## 10. Verify, then question
Read `tests/test_core.py`, `tests/test_contracts.py`, `tests/test_integration.py`, and `web/e2e/report.spec.ts`. They check distinct claims: algorithm contracts, protocol/goldens, real Blender behavior, and actual browser interaction. A passing constructed fixture does not establish accuracy on arbitrary production files. Read [testing](testing.md), [matching failures](entity-matching.md) and [security](security.md) before making broader claims.
