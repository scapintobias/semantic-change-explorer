# Diff semantics

`unchanged` always means no difference in the fields this version compared. It never means Blender files are globally equivalent. Coverage is the intersection of both snapshots' supported domains, with omissions carried forward to the IR and inspector.

| Record/change | Exact meaning in v0.1 |
|---|---|
| Added / removed | Unclaimed observation without unresolved candidate edges; relative to matcher |
| Matched | One-to-one accepted correspondence with method and evidence |
| Modified | Accepted pair has at least one emitted semantic change |
| Renamed | Names differ on an inferred pair; historical rename is not proven |
| Moved / rotated / scaled | Authored local channels differ beyond tolerance; includes rotation mode context |
| Transformed | Delta channels or parent inverse differ |
| Relationship | Referenced entity set differs after mapping A references to B identities |
| Material | Ordered slots / sampled parameters or per-polygon slot indices differ |
| Modifier | Ordered stack presence/type/name/visibility/allowlisted settings differ |
| Geometry | Index-compatible authored mesh has vertex displacement above epsilon |
| Topology | Index-sensitive edge/polygon connectivity hash differs |
| Evaluated | Evaluated mesh topology/positions or world matrix differs at saved frame |
| Ambiguous | Remaining candidate edges prevent a supported correspondence |
| Not compared | Domain unsupported or missing on either side; no equivalence claim |

Mesh topology compares vertex index connectivity. It is not mathematical shape equivalence. Face triangulation for GLB rendering is a transport detail and does not overwrite source topology semantics. Reindexing can produce false differences; equal connectivity can also hide a semantic reidentification of individual vertices. Distances are between corresponding indices, in mesh-local Blender units. Changed count includes only distances greater than 1e-5; maximum and mean refer to those changed vertices.

An object moved with an identical local mesh has a transform change, not a mesh edit. A changed bevel can leave the authored mesh untouched while the evaluated mesh changes. The report separates these observations but cannot prove causal attribution: a simultaneous parent, constraint or frame change can also affect evaluation.

Evaluated state: active scene/view layer, saved current frame, evaluated mesh counts/topology/positions/bounds/centroid and evaluated world transform for objects. Constraints may influence that result while their settings remain not compared. No simulation playback, animation trajectory, bake reconstruction or driver-source comparison is attempted. Script-disabled evaluation can differ from an artist's trusted Blender session.

Material coverage is deliberately limited: slot names, diffuse color, metallic/roughness, first Principled node's base-color/metallic/roughness defaults and linked-input flags, plus polygon material slot indices. Linked defaults are not claimed as rendered shader output. Texture pixels and node connections are not compared. Modifier settings are allowlisted for Bevel, Subdivision Surface, Solidify, Mirror and Array; other types retain presence/order/name/visibility with settings disclosed as not compared.
