"""Four commands supporting comparison, debugging and local viewing."""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from .adapters.blender import effects, extract
from .core.diff import compare
from .core.model import read, write
from .report import build_report, serve, viewer_assets


def run(args):
    if args.command == "serve":
        return serve(args.directory, args.port, args.open)
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError(
            f"Output already exists: {output}. Choose a new output path; inputs/reports are never overwritten."
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    if args.command == "snapshot":
        with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
            staged = Path(tmp) / "snapshot.json"
            extract(args.source, staged, blender=args.blender)
            shutil.move(staged, output)
    elif args.command == "compare-snapshots":
        a, b = read(args.before), read(args.after)
        ir, _ = compare(a, b, effects if a["adapter"]["name"] == "blender" else None)
        write(output, ir)
        print(json.dumps(ir["summary"]))
    else:
        viewer_assets()
        with tempfile.TemporaryDirectory(prefix="sce-", dir=output.parent) as tmp:
            stage = Path(tmp) / "report"
            stage.mkdir()
            a, ta = extract(
                args.before, stage / "a.snapshot.json", stage / "a.glb", args.blender
            )
            b, tb = extract(
                args.after, stage / "b.snapshot.json", stage / "b.glb", args.blender
            )
            ir, timings = compare(a, b, effects)
            write(stage / "changes.json", ir)
            build_report(stage, a, b, ir, {"before": ta, "after": tb, **timings})
            shutil.move(stage, output)
        print(json.dumps(ir["summary"]))
        print(f"Report: {output}\nView: sce serve {output}")


def main():
    parser = argparse.ArgumentParser(
        prog="sce", description="Understand changes between two local structured scenes"
    )
    parser.add_argument(
        "--debug", action="store_true", help="show a traceback on failure"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("compare", "compare-snapshots", "snapshot"):
        p = sub.add_parser(command)
        if command == "snapshot":
            p.add_argument("source")
        else:
            p.add_argument("before")
            p.add_argument("after")
        p.add_argument("--output", "-o", required=True)
        if command != "compare-snapshots":
            p.add_argument("--blender")
    p = sub.add_parser("serve")
    p.add_argument("directory")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--open", action="store_true")
    args = parser.parse_args()
    try:
        run(args)
    except Exception as exc:
        if args.debug:
            raise
        print(
            f"sce: {str(exc).splitlines()[0]}\nUse --debug before the command for technical details.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
