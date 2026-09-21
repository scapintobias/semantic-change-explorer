# Verification

## Fast host tests

```sh
python -m pip install jsonschema
python -m unittest discover -s tests -v
```

Core tests need no Blender. Contract tests compare actual stored snapshots with the complete expected IR. JSON Schema checks are explicitly skipped if the optional `jsonschema` development dependency is missing. Integration is explicitly skipped unless requested; a skip is not a successful Blender test.

## Real Blender integration

```sh
SCE_INTEGRATION=1 python -m unittest discover -s tests -v
```

The test creates fresh files in a temporary directory, extracts A/B, re-extracts A, checks byte-identical canonical snapshots, checks source SHA-256 before/after, verifies the registered script sentinel remains absent, verifies expected semantic categories/summary and parses GLB JSON chunks to confirm exported entity IDs. Set `BLENDER` if the executable is not on PATH or at the supported macOS location. This is a behavioral autoexec test, not a native-code security audit.

## Viewer

```sh
npm ci --prefix web
npm test --prefix web
npm run build --prefix web
sce serve outputs/demo
# Separate terminal, with the server running:
npm run test:e2e --prefix web
```

The pure Node tests cover comparison endpoints, filtering, navigation and safe string formatting. Playwright loads actual generated GLBs in Chrome, asserts selection/inspection, modes, slider, filters, keyboard navigation and raycast selection, and rejects page errors or external requests. `CHROME_PATH` selects an installed Chromium executable outside the default macOS Chrome path. Screenshot output is `docs/demo.png` and is captured after actual loading. No fake scene/render is supplied to the browser test.

## Golden discipline

`fixtures/before.snapshot.json`, `after.snapshot.json` and `expected-change.json` are complete examples from the actual fixture. `expected-summary.json` asserts semantic outcome independently of nondeterministic Blender save-byte hashes. Changing a golden requires explaining the behavior change in `docs/build-log.md` and reviewing the changes, not running a blind regeneration flag. Topology hashes were strengthened to include isolated vertex count; relationship records gained machine-readable reference IDs. Those changes require updated example goldens without changing the seven intended edited entities.

## What this does not prove

No user research, adversarial asset corpus, shader fidelity test, 2 GB scene benchmark, cross-browser matrix, screen-reader audit, Blender 4.2 local validation or Windows run has been completed. CI definitions are supplied but are not evidence of hosted runs. Tests exercise important contracts rather than all Blender property combinations. Unsupported domains remain declared in every report.

Local results: the final 25-test Python suite passes with installed Blender 4.4.0. The real integration test also passed on Blender 4.5.14 LTS (the complete 24-test suite before the final pure-core identical-observation fast-path test was added). Six Node utility tests and the real Chrome interaction test passed. The LTS image was retrieved from the official release archive and SHA-256 verified before use.
