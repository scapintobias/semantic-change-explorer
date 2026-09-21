# Licensing decision — checked 2026-09-21

Project code is **GPL-3.0-or-later**; the full GPL v3 text is in `LICENSE`. Later versions are permitted by the project license declaration. This is a conservative release decision, not a legal opinion about every possible process boundary.

The [Blender Foundation's license guidance](https://www.blender.org/about/license/) states that published scripts using its Python API require GPL-compliant licensing. Its distributed binaries use GPL v3 or later. The Blender extractor imports `bpy`, so treating it as proprietary or automatically exempt would be unjustified. The entire small project uses one compatible license to avoid asserting a contested separation between adapter and host.

[Blender Extensions Platform](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html) requirements are relevant if an extension is ever distributed there. This repository is an external CLI/report product, not an extension submission; no compliance claim for an extension package is made.

The external process boundary is an engineering/testability boundary, not a declaration that copyleft does or does not cross it. A future separately licensed core would require separate review. We did not reuse competitor source or copy Blender's `blend2json.py` implementation. Blender is located on the user's machine and is not bundled.

React, React DOM, Scheduler and Three.js runtime code use MIT licenses. Their notices are copied verbatim into the packaged viewer and reports by `scripts/package_viewer.py`. TypeScript, Vite and build/test dependencies are development tooling; their licenses remain in installed packages. No remote fonts, icons, proprietary UI kit or texture assets are bundled. The hero image is captured from our generated fixture and actual viewer.

Input files and resulting source-derived report content are not automatically relicensed as GPL by processing. Users remain responsible for rights in their own assets. Distributing compiled viewer code still carries the project and dependency license obligations; distribute corresponding source and build instructions alongside any binary release. See [ADR 006](decisions/006-licensing.md).
