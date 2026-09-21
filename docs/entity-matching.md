# Entity correspondence

We have two observations, not a durable identity ledger. The name “Housing” can be reused after deleting an object; a renamed object can still be the same thing. The matcher therefore emits correspondence evidence and uncertainty rather than treating names as IDs.

## The actual algorithm

The pipeline first pairs identical captured entity states when source provenance and the complete entity observations are identical, without heuristic scoring. This is exact observed state, not historical identity. Otherwise, `core/matching.py:evidence` rejects different types. It ranks remaining candidate pairs using exact name +4, identical quantized local geometry +6, identical topology +2, linked data name +2, context +1, material-name slots +1, and tolerant spatial equality +1. Empty hints add nothing. Candidate threshold is 5. These weights are hand-chosen ranking priorities, not calibrated probabilities.

`match` accepts a pair only when each side is the other's unique best candidate by a margin of at least 2 points. Both sides are removed together; candidates are reconsidered until no more safe pairs emerge. Remaining candidate edges are exported as ambiguity. Unmatched entities with no remaining candidate become added or removed relative to this matcher. No maximum-weight assignment is used: maximizing a total would force choices we do not have evidence to justify.

One-to-one correspondence is an invariant. Iteration and serialization are stable. Candidate construction uses O(A×B) time/memory; ranking is linear per acceptance round, worst-case O(min(A,B)×A×B). This can be expensive with repeated components. No spatial search index exists yet.

## Confidence vocabulary

- **Exact state**: equal entity observation in equal source provenance. This is not a persistent-identity guarantee across independent files or linked resources.
- **Strong inferred**: accepted same-name pair supported by additional evidence. A replacement with copied name/context can still fool it.
- **Probable rename**: accepted different-name pair. The inspector displays evidence. The `renamed` category means a name difference on this inferred pair.
- **Ambiguous**: plausible candidate edges remain without sufficient separation; both observations stay visible.
- **Unmatched**: no accepted or unresolved candidate. Addition/removal is an interpretation of evidence, not proof of editing history.

## Worked examples

1. **Same name, moved**: Body keeps geometry/topology/data/context/material hints. It loses the spatial equality point, but name support separates it from other candidates. The diff reports local position and evaluated world transform changes; no local mesh change.
2. **Renamed, identical**: Body → Housing loses +4 name, retains +6 geometry plus structural evidence. A unique candidate is a probable rename. No invented numerical confidence is shown.
3. **Renamed and slightly moved**: same geometry and context still provide 7 points; a unique pair exceeds threshold and margin. Example covered by `test_rename_and_move`.
4. **Deleted A, unrelated B**: changed name, geometry and context, no meaningful shared hints: score below 5. Two unmatched records are emitted.
5. **Two near-identical objects**: equal evidence to both targets produces a zero margin. Four candidate edges can remain. We do not choose the first alphabetically.
6. **Duplicate objects**: distinct retained names can separate otherwise equal geometry. If names also change symmetrically, geometry equality alone does not establish which duplicate is which.
7. **Shared mesh**: geometry fingerprints repeat because several objects use one datablock. Name/context/transform evidence can separate them. Shared data is not treated as object identity.

The real fixture deliberately renames two equal washers, changes their data names and moves both to a shared location. The report shows four ambiguous observations rather than two asserted renames.

## Failure cases

Geometry hashes depend on indexing and six-decimal rounding. Identical shapes with reordered vertices can lose evidence. Authored geometry, name and context can all be copied to a replacement, yielding a false match. Multiple simultaneous edits can drop a genuine correspondence below threshold. Parent identity is not an iterative graph-matching signal; collection names serve as context, which can itself change. The weights and threshold are tested on constructed cases, not calibrated on a representative corpus. Users cannot override matches in v0.1.
