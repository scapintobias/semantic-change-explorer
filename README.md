<!-- @format -->

# Semantic Change Explorer

Semantic Change Explorer is a local tool for understanding how a 3D scene changes between two Blender files.

It is built for the simple case that matters most: you have a before and after state, you want to know what changed, and you want the answer in a fast, local, human-readable view instead of a raw file diff.

The tool compares two `.blend` files on your own machine, extracts the scene structure, matches corresponding objects, and presents the result in a browser as a structured comparison with 3D views, change summaries, and evidence for likely correspondences.

![Actual generated enclosure comparison](docs/demo.png)

## Why this exists

Most file comparison tools are good at text, binary blobs, or rendered screenshots. They are not very good at helping you reason about a 3D scene as a scene.

This project is aimed at exactly that gap:

- compare a model before and after a design change
- inspect which objects changed and how
- understand whether something was added, removed, renamed, moved, or modified
- review the inferred correspondence between the two states
- do all of it locally, without sending files anywhere

It is not a version-control system, merge tool, or a full Blender diff engine. It is a focused local analysis tool for understanding scene-level changes.

## What it does

- compares two local Blender files directly
- matches objects between the previous and current scene
- highlights added, removed, moved, and modified entities
- surfaces likely rename and ambiguity cases
- shows spatial geometry and semantic property deltas
- keeps the workflow entirely local to your machine

This is especially useful when you are debugging design changes, checking fabrication or assembly updates, or simply trying to understand what changed between two scene states.

## How the local workflow works

The primary workflow is browser-first and local-only:

1. You start the app with `sce-app --open`.
2. You choose a Before and After `.blend` file in the browser.
3. The browser sends those files only to the local loopback service on your own machine.
4. The app stages the files in a temporary workspace.
5. Blender extracts scene data and visual exports locally.
6. The project compares the two states and builds a local report.
7. The same app opens directly into the comparison viewer.

No files leave your computer. Nothing is uploaded to a cloud service. After processing, the temporary job files are cleaned up.

## Install

Requirements:

- Python 3.11+
- Blender 4.2–4.5
- a working Blender executable on PATH, or a valid `BLENDER` environment variable

On a local checkout, the install is straightforward:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Then launch the app:

```sh
sce-app --open
```

This opens the app at `http://127.0.0.1:8765`.

If Blender is not automatically detected, set it explicitly:

```sh
export BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
sce-app --open
```

## Use it

Once the app is running:

- select the Before `.blend`
- select the After `.blend`
- click Compare
- inspect the result in the browser

The viewer includes:

- a 3D comparison view
- A/B/overlay/compare modes
- a change index for found entities
- semantic details for selected objects
- a summary of likely correspondences and ambiguities

## Developer and advanced usage

The browser app is the product workflow. The CLI is still there for optional headless usage and debugging, but it is not the main user experience.

Examples:

```sh
sce compare before.blend after.blend --output ./report
sce serve ./report --open
```

This is useful for reproducible local processing, fixtures, and automation.

## Privacy and local-only operation

This project is designed to stay on your machine.

- no accounts
- no telemetry
- no remote uploads
- no cloud processing
- only the local loopback service is used during comparison

Files are processed in a temporary local workspace and removed after the comparison completes. The security and trust model is intentionally simple: if it is not on your machine, it is not part of the workflow.

See [docs/security.md](docs/security.md) for the implementation boundaries and risk notes.

## Project structure

The repository is organized around a small but clear flow:

- the browser app handles file selection and the user-facing workflow
- the local server handles the loopback-only compare API
- Blender extracts the scene state and visual output
- the comparison engine matches and evaluates scene differences
- the report view renders the result locally

For more detail, start with:

- [docs/architecture.md](docs/architecture.md)
- [docs/code-tour.md](docs/code-tour.md)
- [docs/data-model.md](docs/data-model.md)
- [docs/entity-matching.md](docs/entity-matching.md)
- [docs/testing.md](docs/testing.md)

## Limitations

This is a practical comprehension tool, not a general-purpose Blender history system.

It is designed for useful scene-level understanding, but it has limits:

- heuristic matching can be wrong in ambiguous cases
- it compares a saved scene state, not an edit history
- it does not reconstruct a perfect object timeline
- it focuses on scene semantics, not full rendering or simulation fidelity

That is intentional. The goal is clarity, not pretending to be a full-blown model-diffing platform.

## Contributing

Contributions are welcome. The codebase is structured around a small number of core components, and the best place to start is the architecture and code-tour docs.

See [CONTRIBUTING.md](CONTRIBUTING.md) and the decision records in [docs/decisions/README.md](docs/decisions/README.md).

## License

The project is licensed under the GPL-3.0-or-later.

Third-party notices for bundled viewer dependencies are preserved in the packaged output and the project includes the relevant licensing documentation. See [LICENSE](LICENSE) and [docs/licensing.md](docs/licensing.md).
