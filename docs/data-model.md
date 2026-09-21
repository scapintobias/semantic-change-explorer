# Data model — protocol 1.0

The [snapshot schema](../schemas/snapshot-1.0.schema.json) records observations. The [Change IR schema](../schemas/change-1.0.schema.json) records a comparison of two observations. Tool version 0.1.0 and protocol version 1.0 are different: a patch to UI need not change the protocol.

Snapshot required fields: `schema_version`, `adapter` (name and extractor version), `source` (basename and SHA-256 of file bytes), `coverage`, `entities`. Application version and context describe interpretation. No timestamps or absolute source paths enter the canonical snapshot. Process timings live separately. External resources are not included in the source fingerprint; unchanged file bytes do not guarantee unchanged linked assets.

Trimmed from the canonical fixture (identifiers are snapshot-local):

```json
{"schema_version":"1.0","adapter":{"name":"blender","version":"0.1.0"},
 "context":{"frame":1,"units":"METRIC","unit_scale":0.01,"autoexec_disabled":true},
 "entities":[{"id":"object:00012","type":"blender.mesh","name":"Service panel",
 "properties":{"location":{"value":[0,0,1.35],"category":"moved","label":"Local position","coverage":"transforms"}},
 "relations":{"parent":[],"groups":["collection:00002"]},
 "identity":{"geometry":"…","topology":"…","data":"Cube.002","context":["Instrument assembly"]},
 "visual":{"entity_id":"object:00012"},"extensions":{"blender":{"mesh":{"vertex_count":8},"evaluated":{"vertex_count":96}}}}]}
```

This excerpt omits mandatory provenance/coverage and is illustrative; complete valid examples are [before](../fixtures/before.snapshot.json) and [after](../fixtures/after.snapshot.json).

`id` is unique inside one snapshot only. Ordinal IDs may change when names sort differently. Never join snapshots by this field. `type` is namespaced. `properties` maps adapter-chosen keys to values plus presentation labels, category and coverage key. `relations` maps roles to lists of entity IDs. A role can represent parent, group or a future domain link. `identity` contains evidence hints, not persistent identity. `spatial` and `visual` are optional. `extensions.blender` keeps the neutral core independent of vertices, optics and modifiers.

The authored mesh carries counts, index-sensitive topology hash, quantized position hash, local bounds, centroid and vertex positions. The evaluated mesh has the same structure, plus an evaluated world matrix on the object extension. These arrays permit tolerant displacement comparisons. They also make snapshot size O(vertices); they are not a compact production database.

A trimmed IR record:

```json
{"id":"pair:object:00012","before":"object:00012","after":"object:00011",
 "name":"Service panel","type":"blender.mesh","status":"modified",
 "match":{"confidence":"strong inferred","method":"mutual-best-margin","evidence":["same name (not proof of identity)","same geometry"]},
 "changes":[{"category":"moved","label":"Local position","domain":"authored","before":[0,0,1.35],"after":[0.4,0.2,2.75]}]}
```

See [full IR](../fixtures/expected-change.json) for exact IDs and all evidence. IR also includes source provenance, one-to-one correspondences, unresolved candidate edges, summary counts, extraction contexts and coverage. `ambiguous` records are separate before/after observations, so record counts can exceed either source entity count.

JSON Schema validates shape; runtime validation also checks unique IDs and valid relationship references. The schema deliberately permits adapter extensions. Same adapter name/version is required for comparison; incompatible versions fail rather than guessing migrations. Application versions and units are disclosed in contexts: comparisons across different evaluated environments need human interpretation.

Canonical policy: object keys sorted; entities sorted by adapter IDs; relationship sets sorted; modifier/material/vertex order preserved. Floats rounded to six decimals; comparisons use absolute epsilon 1e-5 in native units with zero relative tolerance. Booleans are not numbers. Non-finite values fail. Rotation is radians and representation-dependent; quaternion sign equivalence and wrapped Euler equivalence are not normalized. Mesh position hashes are identity hints only; change detection uses tolerant numeric distances.
