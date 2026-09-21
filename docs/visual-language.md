# Visual language and interaction

The center is the comparison surface. The left index selects a semantic record; the right inspector explains it. A and B share one orbit camera. The index is navigable rather than a decorative activity feed, and relationships are named explicitly in the inspector. There is no expandable scene tree in v0.1.

| Meaning | Visual and non-color cue |
|---|---|
| Added | B mesh, green tint, `+` marker and “added” text |
| Removed | A mesh remains inspectable, rose tint, `−` marker and “removed” text |
| Modified | `↔` marker, property sections, selection box; source colors retained |
| Ambiguous | Violet tint, `?` marker, unresolved candidates and evidence |
| Selected | Gold bounding box and emissive emphasis in either/both states |
| Position difference | Gold arrow between evaluated world origins; endpoints are observations |
| Topology incompatible | Explicit inspector notice, separate before/after shapes; no morph |
| Unchanged in compared fields | `=` marker; optional removal from viewport/index |

Overlay draws A as a translucent wireframe ghost and B as a solid surface. Wireframe includes GLB triangulation, so its diagonal edges are not evidence of authored topology edits. A-only and B-only show the selected source state. The comparison slider crossfades opacity continuously; it never interpolates vertices or transforms. Intermediate views do not claim a physical transition. No autonomous motion is used, including for fitting; reduced-motion preferences therefore require no animation disable toggle.

Click a mesh to select its record, click a row to highlight the meshes, press F or Fit selected to frame them. `[` and `]` cycle changed records within the active index filters; Previous/Next provide equivalent buttons. Inputs retain their ordinary keyboard behavior. Fit scene restores a shared framing. Orbit: drag; pan: right drag; zoom: wheel. Semantic navigation is fully available without aiming at a 3D object. Camera/light/collection entries have semantic records but no GLB proxy geometry; fit has no effect for these entries.

The index category/search filters affect the index; Changed only also hides unchanged viewport meshes. This permits visual context while narrowing textual search. Selection can persist outside a filter; the inspector remains explicit about the selected name. Dark neutral surfaces and modest spacing prioritize geometry and precise values. Status never depends on hue alone.

Preview scope: evaluated mesh objects only, solid diffuse material colors, no textures/lighting fidelity. The viewport supplies its own lights; Blender camera and light edits are inspected semantically. Geometry fidelity is geometric, not a render comparison. The selected arrow uses Blender Z-up to glTF Y-up coordinate conversion `(x,z,-y)`. Units are native Blender units; display scale settings are provenance, not a baked conversion to meters.

Known limitations: occlusion can make selecting inner parts difficult, transparency sorting can be imperfect, large evaluated meshes are not decimated, and there is no per-vertex heatmap. Opacity comparison is intentionally simpler than interpolating vertices whose identity may be uncertain.
