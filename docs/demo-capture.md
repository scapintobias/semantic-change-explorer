# Reproduce the demo

Run the README fixture/compare/serve commands. Open the local report in a desktop browser at roughly 1600×1000. The default selection is Service panel. Fit scene and use Overlay: its old position is wireframe, new position solid, with a world-position arrow.

For a short recording: start on Service panel; move the A↔B slider between endpoints; select Lower housing to show probable rename and authored/evaluated sections; select Thermal rail to show vertex displacement; select Legacy connector and USB-C module; filter Ambiguous and inspect the spacer candidates. Clear filters and click the geometry to demonstrate reverse selection.

Automated still capture: with the server at port 8765, run `npm run test:e2e --prefix web`. It writes `docs/demo.png` after loading both actual GLBs. The test also checks real raycast selection. No animation recording has been generated; use the above exact sequence with the OS screen recorder if desired. Do not present crossfade as a reconstruction of an edit trajectory.
