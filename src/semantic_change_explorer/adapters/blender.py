"""Host-side Blender process and domain geometry comparison. Does not import bpy."""

import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from ..core.model import EPSILON, equivalent, fingerprint, read


def locate(explicit=None):
    """Resolve a Blender executable; detect version rather than assume PATH."""
    candidate = explicit or os.environ.get("BLENDER") or shutil.which("blender")
    if (
        not candidate
        and Path("/Applications/Blender.app/Contents/MacOS/Blender").exists()
    ):
        candidate = "/Applications/Blender.app/Contents/MacOS/Blender"
    if not candidate:
        raise ValueError(
            "Blender not found. Install Blender or pass --blender /path/to/blender."
        )
    result = subprocess.run(
        [str(candidate), "--version"], capture_output=True, text=True, timeout=30
    )
    found = re.search(r"Blender (\d+)\.(\d+)\.(\d+)", result.stdout)
    if result.returncode or not found:
        raise ValueError("Could not read Blender version; check --blender executable")
    version = tuple(map(int, found.groups()))
    if version < (4, 2, 0) or version >= (5, 0, 0):
        raise ValueError(
            f"Unsupported Blender {found.group(0)}; v0.1 accepts 4.2–4.5. See tested versions in README."
        )
    return str(candidate)


def extract(source, output, visual=None, blender=None, threads=None):
    """Open input in an isolated process, hash before/after, return snapshot/timings."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_file() or source.suffix.lower() != ".blend":
        raise ValueError(f"Expected an existing .blend input: {source}")
    if source == output or (visual and source == Path(visual).resolve()):
        raise ValueError("Output must not overwrite a source file")
    sha = fingerprint(source)
    args = [
        locate(blender),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        str(source),
        "--python-exit-code",
        "3",
        "--python",
        str(Path(__file__).with_name("blender_extract.py")),
        "--",
        str(output),
    ]
    if threads is not None:
        args[4:4] = ["--threads", str(threads)]
    if visual:
        args.append(str(Path(visual).resolve()))
    start = time.perf_counter()
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=300)
    finally:
        if fingerprint(source) != sha:
            raise RuntimeError(
                "Source fingerprint changed during extraction; input may have been edited concurrently"
            )
    if proc.returncode or not output.exists():
        raise RuntimeError(
            "Blender extraction/export failed. Check file integrity and external resources.\n"
            + (proc.stderr + proc.stdout)[-3000:]
        )
    if visual and not Path(visual).is_file():
        raise RuntimeError(
            "GLB export missing; check Blender glTF exporter availability"
        )
    line = next(
        (s for s in proc.stdout.splitlines() if s.startswith("SCE_TIMINGS=")), None
    )
    timings = json.loads(line.split("=", 1)[1]) if line else {}
    timings["process_seconds"] = time.perf_counter() - start
    timings["startup_load_shutdown_seconds"] = max(
        0,
        timings["process_seconds"]
        - sum(
            timings.get(k, 0) for k in ("extraction_seconds", "visual_export_seconds")
        ),
    )
    return read(output), timings


def effects(a, b, coverage):
    """Compare index-compatible meshes; never infer vertex correspondence after reindexing."""
    old = a.get("extensions", {}).get("blender", {})
    new = b.get("extensions", {}).get("blender", {})
    result = []
    for key, domain, required in (
        ("mesh", "authored", "mesh"),
        ("evaluated", "evaluated", "evaluated"),
    ):
        x, y = old.get(key), new.get(key)
        if required not in coverage or x is None or y is None:
            continue
        if x["topology"] != y["topology"]:
            result.append(
                {
                    "category": "topology" if key == "mesh" else "evaluated",
                    "domain": domain,
                    "label": "Mesh topology differs"
                    if key == "mesh"
                    else "Evaluated topology differs",
                    "before": {
                        k: x[k]
                        for k in ("vertex_count", "edge_count", "face_count", "bounds")
                    },
                    "after": {
                        k: y[k]
                        for k in ("vertex_count", "edge_count", "face_count", "bounds")
                    },
                    "compatible": False,
                }
            )
        else:
            distances = [math.dist(v, w) for v, w in zip(x["vertices"], y["vertices"])]
            changed = [d for d in distances if d > EPSILON]
            if changed:
                result.append(
                    {
                        "category": "geometry" if key == "mesh" else "evaluated",
                        "domain": domain,
                        "label": "Vertex positions differ"
                        if key == "mesh"
                        else "Evaluated geometry differs",
                        "before": {"bounds": x["bounds"]},
                        "after": {"bounds": y["bounds"]},
                        "compatible": True,
                        "displacement": {
                            "changed_vertices": len(changed),
                            "max": max(changed),
                            "mean_changed": sum(changed) / len(changed),
                        },
                    }
                )
    if "evaluated" in coverage and not equivalent(
        old.get("evaluated_world"), new.get("evaluated_world")
    ):
        result.append(
            {
                "category": "evaluated",
                "domain": "evaluated",
                "label": "Evaluated world transform differs",
                "before": old.get("evaluated_world"),
                "after": new.get("evaluated_world"),
            }
        )
    return result
