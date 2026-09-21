# Contributing

Use Python 3.11+ and Node 22.18+ (or 24/26). Install Blender separately for integration. Start with the README's clone-directory setup and generated demo. Read [architecture](architecture.md), then [code tour](code-tour.md).

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e . build jsonschema
npm ci --prefix web
npm run build --prefix web
python -m unittest discover -s tests -v
npm test --prefix web
```

Use explicit functions and ordinary state. Python modules use stdlib at runtime; do not introduce `bpy` imports into the core. TypeScript uses strict checking. Prefer meaningful behavioral tests; do not mirror the implementation mechanically. Reproduce a bug before changing a golden.

To add a semantic property: choose the authored/evaluated scope; add an allowlisted extraction property with label/category/coverage; verify it is deterministic; add a fixture edit and assert the resulting Change IR; update coverage docs and inspector presentation if required. Example: add an optical field to the camera allowlist instead of dumping every RNA property. If absent in older snapshots, avoid claiming equality.

To add an adapter conceptually: produce the neutral snapshot contract; choose namespace/types and identity hints; declare coverage and provenance; provide optional domain effects; provide portable visuals with snapshot-ID mapping; register extraction/effects in the CLI. Write a non-Blender unit test before expanding the core. Do not implement another adapter merely to demonstrate extensibility.

A pull request should state the user-visible problem, final behavior, evidence/tests and limits. Include actual screenshots for interaction changes. Disclose source/license provenance for reused code. Do not include private files, generated `.blend` inputs, personal notes, secrets or confidential report content. `private-notes/` is ignored and must stay private. New domain claims require tests and documentation.

Useful first contributions: a deterministic fixture for parent-transformed children, better semantic rendering of nested modifier changes, a measured large-scene indexing strategy, non-mesh viewport proxies, and documented validation on additional LTS/OS combinations. See [roadmap](../ROADMAP.md).
