"""Trusted demo generator, run via Blender --background --python. Writes new files only."""

import argparse
import sys
from pathlib import Path

import bpy

p = argparse.ArgumentParser()
p.add_argument("--output", default="outputs/fixture")
p.add_argument("--scale", type=int, default=0)
args = p.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
out = Path(args.output).resolve()
out.mkdir(parents=True, exist_ok=True)
if any((out / n).exists() for n in ("before.blend", "after.blend")):
    raise RuntimeError("Fixture files already exist; choose a fresh --output directory")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.01
assembly = bpy.data.collections.new("Instrument assembly")
scene.collection.children.link(assembly)
electronics = bpy.data.collections.new("Electronics")
assembly.children.link(electronics)


def material(name, color, metallic=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.metallic = metallic
    m.roughness = 0.35
    return m


slate = material("Ceramic graphite", (0.16, 0.23, 0.28), 0.35)
metal = material("Brushed aluminium", (0.62, 0.7, 0.73), 0.7)
orange = material("Signal amber", (0.95, 0.32, 0.055))
green = material("Circuit board", (0.055, 0.34, 0.23))


def part(name, loc, size, mat, collection=assembly, bevel=0.07):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for c in list(o.users_collection):
        c.objects.unlink(o)
    collection.objects.link(o)
    o.data.materials.append(mat)
    if bevel:
        m = o.modifiers.new("Edge radius", "BEVEL")
        m.width, m.segments = bevel, 3
    return o


base = part("Housing", (0, 0, 0), (5.5, 3.5, 0.6), slate)
base["part_number"] = "SCE-001"
panel = part("Service panel", (0, 0, 1.35), (5.25, 3.25, 0.22), metal)
board = part("Controller", (0, 0, 0.5), (3.8, 2.1, 0.12), green, electronics)
rail = part("Thermal rail", (-2, 0, 0.7), (0.3, 2.7, 0.55), metal)
part("Legacy connector", (2.85, -0.7, 0.35), (0.7, 0.75, 0.5), slate)
knob = part("Status lens", (1.6, -1.7, 0.7), (0.7, 0.18, 0.35), orange)
for i in range(3):
    part(
        f"IC {i + 1}",
        (-0.9 + i * 0.9, 0, 0.7),
        (0.55, 0.7, 0.22),
        slate,
        electronics,
        0.03,
    )
for i, x in enumerate((-2.3, 2.3)):
    for j, y in enumerate((-1.3, 1.3)):
        part(f"Fastener {i}{j}", (x, y, 0.9), (0.18, 0.18, 0.8), metal, bevel=0.04)
# Symmetric, indistinguishable naming changes: ambiguity should survive.
for i, y in enumerate((-0.5, 0.5)):
    part(f"Washer {i + 1}", (3.7, y, 0.2), (0.35, 0.35, 0.12), metal, bevel=0)
bpy.ops.object.camera_add(location=(9, -10, 9))
bpy.context.object.name = "Inspection camera"
scene.camera = bpy.context.object
bpy.ops.object.light_add(type="AREA", location=(0, 0, 8))
bpy.context.object.name = "Bench light"
bpy.context.object.data.energy = 800
for i in range(args.scale):
    part(
        f"Scale component {i:04d}",
        (i % 20 * 0.3, i // 20 * 0.3 + 6, 0),
        (0.15, 0.15, 0.15),
        metal,
        bevel=0,
    )
# Safety sentinel: registered text would create a marker if autoexec were enabled.
t = bpy.data.texts.new("autoexec_sentinel.py")
t.write(
    "from pathlib import Path\nPath("
    + repr(str(out / "AUTOEXEC_RAN"))
    + ").write_text('unsafe')\n"
)
t.use_module = True
bpy.ops.wm.save_as_mainfile(filepath=str(out / "before.blend"))
base.name = "Lower housing"
base["part_number"] = "SCE-001-B"
base.modifiers[0].width = 0.18
panel.location += __import__("mathutils").Vector((0.4, 0.2, 1.4))
panel.rotation_euler.z = 0.12
for v in rail.data.vertices:
    if v.co.z > 0:
        v.co.x += 0.15
board.parent = base
knob.data.materials.clear()
knob.data.materials.append(metal)
bpy.data.objects.remove(bpy.data.objects["Legacy connector"], do_unlink=True)
part("USB-C module", (2.95, 0.65, 0.45), (0.8, 1.0, 0.4), orange)
bpy.data.objects["Inspection camera"].data.lens = 65
bpy.data.objects["Bench light"].data.energy = 1100
for i in range(2):
    o = bpy.data.objects[f"Washer {i + 1}"]
    o.name = f"Spacer {i + 1}"
    o.data.name = f"New mesh {i + 1}"
    o.location.y = 0
bpy.ops.wm.save_as_mainfile(filepath=str(out / "after.blend"))
print("Fixture:", out)
