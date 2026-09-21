# Observed performance — 2026-09-21

Environment: Apple M1 Ultra, 64 GiB RAM, macOS 27.0 (26A428), Blender 4.4.0, host Python 3.14.6, Node 26.4.0. Development commands ran with warm local caches and no controlled CPU/load isolation. These are individual observations, not statistical benchmarks or a promise of “fast.”

| Phase | Canonical A | Canonical B | 400-component A | 400-component B |
|---|---:|---:|---:|---:|
| Extraction | 0.026 s | 0.027 s | 0.252 s | 0.254 s |
| GLB export | 0.119 s | 0.118 s | 0.504 s | 0.485 s |
| Startup + file load + shutdown residual | 0.573 s | 0.560 s | 0.601 s | 0.601 s |
| Whole Blender process | 0.718 s | 0.705 s | 1.357 s | 1.340 s |

Canonical matching: 0.0015 s; diff: 0.0012 s. Scale matching: 1.013 s; diff: 0.0188 s. The scale fixture adds 400 simple mesh objects to each input (420 total semantic entities per side including collections/camera/light). Report disk sizes observed were approximately 3 MiB canonical and 17 MiB scale, including an extra stale development bundle in the first canonical report; final packaged sizes can differ.

The browser's actual load-to-both-GLBs-ready display read 0.14 s in the successful initial Chrome run. It starts after the report JSON/JS is loaded, so it is not a full navigation-to-interactive metric. DevTools/Playwright navigation timing is needed for that wider measure. No memory peak, p95 or cold-start claim is made.

Timings are written to each report's `timings.json`. The host times the whole subprocess; the trusted extractor reports extraction and export durations; their residual aggregates startup, source loading and shutdown. It does not independently measure Blender startup. Matching/diff use `perf_counter`. Browser geometry readiness uses `performance.now`. Timings are outside canonical semantic snapshots to preserve determinism.

Reproduce a many-object test:

```sh
blender --background --factory-startup --disable-autoexec --python-exit-code 3 \
  --python scripts/generate_fixture.py -- --output outputs/scale-fixture --scale 400
sce compare outputs/scale-fixture/before.blend outputs/scale-fixture/after.blend --output outputs/scale-report
```

Choose new directories for another run. The fixture is intentionally low-poly; it measures candidate density and per-object/export overhead, not 2 GB assets, heavy simulation or many-million-vertex meshes. Matching holds O(A×B) candidate data and can require O(min(A,B)×A×B) time. JSON vertex arrays and GLB mesh copies also consume memory. No streaming, memory cap, preview LOD or broad-phase candidate index is implemented. The next optimization should follow a measured real-scene bottleneck, not a generic speed claim.
