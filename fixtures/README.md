# Canonical enclosure revision

The complete JSON snapshots and expected Change IR are checked in; private assets and generated `.blend` binaries are not. `scripts/generate_fixture.py` creates a bench instrument with a base housing, floating service panel, controller, thermal rail, fasteners, connector, lens, camera/light and collections.

B deliberately: renames Housing to Lower housing and changes its custom part number/bevel width; moves/rotates Service panel; edits upper Thermal rail vertices; reparents Controller; changes Status lens material; removes Legacy connector; adds USB-C module; changes camera lens/light energy; renames and converges equal washers so correspondence remains ambiguous. Bevel changes demonstrate authored versus evaluated state; the rail demonstrates compatible-topology vertex displacement.

Expected: seven modified records, one added, one removed, ten unchanged, four ambiguous observations. Ambiguity is counted per unmatched-side record, not per hypothetical pair. A registered text-block sentinel must never execute during extraction. The generator itself is trusted repository code.

`--scale 400` adds 400 small mesh components to each file. It is a many-object test, not a high-poly production benchmark. Golden updates require a build-log reason and semantic review.
