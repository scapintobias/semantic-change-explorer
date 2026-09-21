"""Runs ONLY inside disposable Blender. No save operation; stdlib + bpy only.

Authored properties are allowlisted. Evaluated geometry is sampled at the saved
frame using the active view layer, separately from mesh datablocks.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import bpy

START = time.perf_counter()
ROUND = 6


def clean(v):
    if isinstance(v, float):
        return round(v, ROUND) or 0.0
    if isinstance(v, dict):
        return {k: clean(x) for k, x in sorted(v.items())}
    if isinstance(v, (list, tuple)) or hasattr(v, "to_list"):
        return [clean(x) for x in v]
    if isinstance(v, (str, int, bool)) or v is None:
        return v
    if hasattr(v, "to_dict"):
        return clean(v.to_dict())
    if hasattr(v, "__len__") and hasattr(v, "__getitem__"):
        return [clean(x) for x in v]
    return None


def digest(v):
    return hashlib.sha256(
        json.dumps(clean(v), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def mesh_info(mesh):
    vertices = [clean(list(v.co)) for v in mesh.vertices]
    topology = {
        "vertex_count": len(vertices),
        "edges": [list(e.vertices) for e in mesh.edges],
        "faces": [list(p.vertices) for p in mesh.polygons],
    }
    return {
        "vertices": vertices,
        "vertex_count": len(vertices),
        "edge_count": len(mesh.edges),
        "face_count": len(mesh.polygons),
        "topology": digest(topology),
        "geometry": digest(vertices),
        "bounds": [
            [min((v[i] for v in vertices), default=0) for i in range(3)],
            [max((v[i] for v in vertices), default=0) for i in range(3)],
        ],
        "centroid": [
            sum(v[i] for v in vertices) / max(1, len(vertices)) for i in range(3)
        ],
    }


def main():
    output = Path(sys.argv[sys.argv.index("--") + 1])
    visual = (
        sys.argv[sys.argv.index("--") + 2]
        if len(sys.argv) > sys.argv.index("--") + 2
        else None
    )
    if bpy.context.preferences.filepaths.use_scripts_auto_execute:
        raise RuntimeError("Refusing extraction: automatic script execution is enabled")
    scene = bpy.context.scene
    objects = sorted(
        scene.objects,
        key=lambda o: (o.name_full, o.library.filepath if o.library else ""),
    )
    object_ids = {o: f"object:{i:05d}" for i, o in enumerate(objects)}
    collections = sorted(
        {c for o in objects for c in o.users_collection}, key=lambda c: c.name_full
    )

    # Include empty and nested collections as semantic entities.
    def collect(c):
        for child in c.children:
            if child not in collections:
                collections.append(child)
            collect(child)

    collect(scene.collection)
    collections.sort(key=lambda c: c.name_full)
    collection_ids = {c: f"collection:{i:05d}" for i, c in enumerate(collections)}
    entities = []
    warnings = []
    for c in collections:
        parents = [collection_ids[p] for p in collections if c.name in p.children]
        entities.append(
            {
                "id": collection_ids[c],
                "type": "blender.collection",
                "name": c.name,
                "identity": {"context": "active-scene"},
                "relations": {"parent": parents},
                "properties": {
                    "visibility": {
                        "coverage": "structure",
                        "category": "visibility",
                        "label": "Collection visibility (viewport / render)",
                        "value": [c.hide_viewport, c.hide_render],
                    }
                },
                "extensions": {},
            }
        )
    graph = bpy.context.evaluated_depsgraph_get()
    modifier_fields = {
        "BEVEL": ["width", "segments", "limit_method", "angle_limit"],
        "SUBSURF": ["levels", "render_levels", "subdivision_type"],
        "SOLIDIFY": ["thickness", "offset"],
        "MIRROR": ["use_axis", "use_clip", "merge_threshold"],
        "ARRAY": ["count", "relative_offset_displace", "use_relative_offset"],
    }
    for o in objects:
        properties = {}

        def prop(key, value, category, label, coverage):
            properties[key] = {
                "value": clean(value),
                "category": category,
                "label": label,
                "coverage": coverage,
            }

        prop("location", list(o.location), "moved", "Local position", "transforms")
        prop(
            "rotation",
            list(o.rotation_quaternion)
            if o.rotation_mode == "QUATERNION"
            else list(o.rotation_axis_angle)
            if o.rotation_mode == "AXIS_ANGLE"
            else list(o.rotation_euler),
            "rotated",
            "Local rotation",
            "transforms",
        )
        prop(
            "rotation_mode",
            o.rotation_mode,
            "rotated",
            "Rotation representation",
            "transforms",
        )
        prop("scale", list(o.scale), "scaled", "Local scale", "transforms")
        prop(
            "matrix_parent_inverse",
            [list(row) for row in o.matrix_parent_inverse],
            "transformed",
            "Parent inverse matrix",
            "transforms",
        )
        prop(
            "delta",
            {
                "location": list(o.delta_location),
                "rotation_euler": list(o.delta_rotation_euler),
                "rotation_quaternion": list(o.delta_rotation_quaternion),
                "scale": list(o.delta_scale),
            },
            "transformed",
            "Delta transforms",
            "transforms",
        )
        prop(
            "visibility",
            [o.hide_viewport, o.hide_render, o.hide_get()],
            "visibility",
            "Hidden in viewport / render / view layer",
            "structure",
        )
        prop(
            "custom",
            {k: clean(o[k]) for k in o.keys() if k != "_RNA_UI"},
            "custom",
            "Custom properties",
            "custom",
        )
        slots = []
        for slot in o.material_slots:
            mat = slot.material
            if mat is None:
                slots.append(None)
                continue
            basic = {
                "name": mat.name,
                "diffuse": list(mat.diffuse_color),
                "metallic": mat.metallic,
                "roughness": mat.roughness,
            }
            if mat.use_nodes:
                bsdf = next(
                    (n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"),
                    None,
                )
                if bsdf:
                    basic["principled"] = {
                        k: clean(
                            list(bsdf.inputs[k].default_value)
                            if k == "Base Color"
                            else bsdf.inputs[k].default_value
                        )
                        for k in ("Base Color", "Metallic", "Roughness")
                    }
                    basic["linked_inputs"] = [
                        k
                        for k in ("Base Color", "Metallic", "Roughness")
                        if bsdf.inputs[k].is_linked
                    ]
            slots.append(basic)
        prop(
            "materials",
            slots,
            "material",
            "Material slots and sampled parameters",
            "materials",
        )
        modifiers = []
        for m in o.modifiers:
            modifiers.append(
                {
                    "name": m.name,
                    "type": m.type,
                    "viewport": m.show_viewport,
                    "render": m.show_render,
                    "settings": {
                        k: clean(getattr(m, k)) for k in modifier_fields.get(m.type, [])
                    },
                }
            )
            if m.type not in modifier_fields:
                warnings.append(f"modifier settings: {m.type}")
        prop("modifiers", modifiers, "modifier", "Ordered modifier stack", "modifiers")
        ext = {}
        if o.type == "MESH":
            ext["mesh"] = mesh_info(o.data)
            prop(
                "face_materials",
                [p.material_index for p in o.data.polygons],
                "material",
                "Polygon material slot assignment",
                "materials",
            )
            evaluated = o.evaluated_get(graph)
            try:
                ext["evaluated"] = mesh_info(evaluated.to_mesh())
            finally:
                evaluated.to_mesh_clear()
        elif o.type == "CAMERA":
            prop(
                "camera",
                {
                    k: getattr(o.data, k)
                    for k in (
                        "type",
                        "lens",
                        "sensor_width",
                        "sensor_height",
                        "clip_start",
                        "clip_end",
                        "ortho_scale",
                        "shift_x",
                        "shift_y",
                    )
                },
                "camera",
                "Camera optics",
                "camera-light",
            )
        elif o.type == "LIGHT":
            prop(
                "light",
                {
                    "type": o.data.type,
                    "energy": o.data.energy,
                    "color": list(o.data.color),
                    "size": getattr(o.data, "size", None),
                    "spot_size": getattr(o.data, "spot_size", None),
                },
                "light",
                "Light parameters",
                "camera-light",
            )
        elif o.type != "EMPTY":
            warnings.append(f"object data: {o.type}")
        world = [list(row) for row in o.evaluated_get(graph).matrix_world]
        ext["evaluated_world"] = world
        entities.append(
            {
                "id": object_ids[o],
                "name": o.name,
                "type": "blender." + o.type.lower(),
                "properties": properties,
                "relations": {
                    "parent": [object_ids[o.parent]] if o.parent in object_ids else [],
                    "groups": sorted(collection_ids[c] for c in o.users_collection),
                },
                "spatial": {"matrix": [list(row) for row in o.matrix_local]},
                "visual": {"entity_id": object_ids[o]},
                "identity": {
                    "geometry": ext.get("mesh", {}).get("geometry"),
                    "topology": ext.get("mesh", {}).get("topology"),
                    "data": o.data.name if o.data else None,
                    "context": sorted(c.name for c in o.users_collection),
                    "materials": [s["name"] if s else None for s in slots],
                },
                "extensions": {"blender": ext},
            }
        )
    source = Path(bpy.data.filepath)
    with source.open("rb") as stream:
        sha = hashlib.file_digest(stream, "sha256").hexdigest()
    snapshot = {
        "schema_version": "1.0",
        "adapter": {"name": "blender", "version": "0.1.0"},
        "application": {"name": "Blender", "version": bpy.app.version_string},
        "source": {"name": source.name, "sha256": sha},
        "context": {
            "scene": scene.name,
            "frame": scene.frame_current,
            "view_layer": bpy.context.view_layer.name,
            "units": scene.unit_settings.system,
            "unit_scale": scene.unit_settings.scale_length,
            "autoexec_disabled": True,
            "libraries": sorted(
                Path(library.filepath).name for library in bpy.data.libraries
            ),
            "external_resources_fingerprinted": False,
        },
        "coverage": {
            "compared": [
                "structure",
                "transforms",
                "mesh",
                "evaluated",
                "materials",
                "modifiers",
                "camera-light",
                "custom",
            ],
            "not_compared": sorted(
                set(
                    [
                        "animation curves, drivers and NLA",
                        "constraints settings",
                        "material node graph internals and textures",
                        "UVs, vertex attributes and normals",
                        "other scenes and view layers",
                        "instances, rigs, simulation caches",
                        "linked resource content provenance",
                    ]
                    + warnings
                )
            ),
        },
        "entities": sorted(entities, key=lambda e: e["id"]),
    }
    output.write_text(
        json.dumps(
            clean(snapshot),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    extracted = time.perf_counter()
    if visual:
        # Preview-only in-memory mutation, after semantic extraction. No source save.
        # Replace arbitrary materials with sampled solid colors: avoid image IO and
        # unsupported shader translation. Convert evaluated meshes to freeze frame.
        bpy.ops.object.select_all(action="DESELECT")
        copies = []
        for o in objects:
            if o.type != "MESH":
                continue
            mesh = bpy.data.meshes.new_from_object(
                o.evaluated_get(graph), depsgraph=graph
            )
            copy = bpy.data.objects.new("preview_" + object_ids[o], mesh)
            scene.collection.objects.link(copy)
            copy.matrix_world = o.evaluated_get(graph).matrix_world.copy()
            copy["sce_entity"] = object_ids[o]
            colors = []
            for slot in o.material_slots:
                colors.append(
                    list(slot.material.diffuse_color)
                    if slot.material
                    else [0.5, 0.5, 0.5, 1]
                )
            mesh.materials.clear()
            for i, color in enumerate(colors or [[0.5, 0.5, 0.5, 1]]):
                material = bpy.data.materials.new(f"preview_{object_ids[o]}_{i}")
                material.diffuse_color = color
                mesh.materials.append(material)
            copy.select_set(True)
            copies.append(copy)
        bpy.ops.export_scene.gltf(
            filepath=visual,
            export_format="GLB",
            use_selection=True,
            export_extras=True,
            export_animations=False,
            export_cameras=False,
            export_lights=False,
            export_materials="EXPORT",
            export_yup=True,
        )
    print(
        "SCE_TIMINGS="
        + json.dumps(
            {
                "extraction_seconds": extracted - START,
                "visual_export_seconds": time.perf_counter() - extracted,
            }
        )
    )


if __name__ == "__main__":
    main()
