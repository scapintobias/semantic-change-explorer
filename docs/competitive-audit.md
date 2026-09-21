# Competitive audit — 2026-09-21

Research preceded implementation. Scope is public product documentation, not reverse engineering. No competitor code, architecture or UI was copied. This is a bounded search, not a claim of universal novelty.

| Tool / primary source | Existing capability and overlap | Decision / distinction |
|---|---|---|
| [BlenDiff](https://github.com/Vishrut2403/blendiff) | Semantic scene comparison, stored snapshots, persistent IDs, broad Blender domains, merge and HTML reports. Current README explicitly covers geometry, materials, rigs, modifiers, animation and collections. | Do not compete on property coverage, snapshot history or merge. Our differentiating hypothesis is the combination of external spatial inspection, arbitrary input pairs, uncertainty and authored/evaluated separation. Arbitrary-file comparison alone is not a defensible novelty claim. |
| [blend2json.py](https://github.com/blender/blender/blob/main/tools/utils/blend2json.py) | Blender-owned structural DNA/block JSON dumper, validation and filtering; warns of address noise and potentially huge output. | Learn that structural serialization is not domain explanation. Use Blender's supported runtime to evaluate a scene, not our own binary parser. No source reuse. |
| [Git LFS](https://git-lfs.com/) | Large-file pointers and storage transport alongside Git. | Complementary storage infrastructure. We explain two states; no repository/history/hosting layer. |
| [Node Differ](https://superhivemarket.com/products/node-differ) | Vendor describes node/property/link comparison against external files or snapshots. | Confirms arbitrary-file workflows already exist. Do not duplicate node-graph diffing. |
| [Innerscene viewer](https://www.innerscene.com/tools/blend-viewer) | Vendor describes local browser parsing and viewing; explicitly cannot recompute modifiers/Geometry Nodes. | Browser viewing alone is not unique. Use Blender evaluation; accept installed-runtime cost. |
| [Blend4Web](https://github.com/TriumphLLC/Blend4Web) | General interactive browser visualization/export. | Visualization transport is established. Our work is comparison semantics and interaction. |

No inspected primary source established the complete differentiated combination. That supports building an experiment, not claiming first-in-market. User usefulness, matching trust and whether spatial overlays outperform lists remain untested hypotheses. Future research should evaluate direct mesh comparison products as well; geometry-distance tools are adjacent, not evidence of authored-scene causality.
