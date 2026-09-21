# Dependency rationale

Host runtime: Python 3.11+ standard library only. Blender is a separately installed application. The production extractor imports standard library modules and `bpy`; no pip install inside Blender is required. Exact JS versions and transitive dependencies are locked by `web/package-lock.json`.

| Runtime dependency | Purpose / why needed | Alternative considered | If unavailable |
|---|---|---|---|
| Blender and `bpy` | Read native semantics and evaluate modifiers with Blender's own rules | Parse `.blend` ourselves; loses authoritative dependency-graph evaluation | Snapshot-only core still works; `.blend` extraction fails actionably |
| React + React DOM | Keep selection, filters and inspector synchronized with accessible ordinary DOM controls | Vanilla DOM is smaller but requires manual reconciliation across interacting panels | Browser interface must be rewritten; file protocol remains valid |
| Scheduler (transitive React dependency) | React runtime scheduling | Use React's supported dependency graph rather than replacing internals | React rendering unsupported |
| Three.js | GLB loading, cameras, transforms, picking and rendering | Raw WebGL substantially increases graphics code; larger engines exceed scope | Semantic JSON remains usable; spatial viewport unavailable |

Blender's bundled glTF exporter is used rather than implementing GLB serialization. Evaluated mesh copies preserve frame and mapping. Standard browser/Python libraries do not provide these 3D facilities.

Development tools: TypeScript catches interface mistakes; Vite/@vitejs/plugin-react bundle local assets; `@types/*` describe APIs; Playwright verifies real browser interaction. Python `setuptools` builds/install packages, `build` verifies distributions, `jsonschema` validates published example contracts. `unittest` provides core/integration tests without a test framework dependency. The Node built-in test runner checks pure viewer semantics.

All libraries are replaceable at a defined boundary, but replacement is not cost-free. The JSON protocol and GLB assets are the stable exchange surfaces. No runtime CDN, remote font or internet API is needed. Installation fetches declared packages; runtime comparison does not intentionally contact the network. Blender itself is not network-sandboxed.

Third-party license notices are bundled by `scripts/package_viewer.py`. `npm audit` at initial install reported zero vulnerabilities; this is a timestamped check, not a security guarantee.

Readability tools used during development: pinned Prettier 3.6.2 for TypeScript/JSX/CSS and Ruff for Python formatting. Neither is imported by the runtime or required to view a report.
