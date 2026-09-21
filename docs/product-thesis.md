# Product thesis

A file can change in bytes while remaining visually identical. A tiny parameter change can also produce a large geometric difference. A reviewer needs to connect the two levels. The product question is how to understand a change, not how to store another version.

Git gives durable file history, and Git LFS can transport large binary files. Neither interprets a Blender modifier or provides a world-space comparison by itself. Textual structural dumps expose implementation details; they often obscure the difference between an authored edit and an evaluated result. Existing semantic Blender tools already solve substantial parts of this problem: see [competitive audit](competitive-audit.md). Our thesis is narrower than “Blender needs version control.”

The experiment is a local instrument for examining any two files that were never prepared for our tool. It places the visual difference, matching evidence and semantic explanation together. Blender is the first adapter because its own API can give us both source mesh data and dependency-graph results. We accept the runtime dependency to avoid independently reverse-engineering its file format and evaluation rules.

The neutral model has entities, named relationships, typed properties and adapter-owned extensions. It does not require mesh data. A future adapter could describe a circuit component or a document section. Only Blender is implemented, so cross-domain usefulness remains a hypothesis, supported by a nonspatial core test rather than production adoption.

Evidence: this repository can generate a known scene revision, extract real files, detect designed changes, and display evaluated geometry. Hypotheses: spatial overlays improve review speed; exposing uncertainty improves decisions; the abstraction transfers to other authoring tools. No user study, usage figures or time-saving claim exists.

Non-goals: history storage, automatic merge, remote collaboration, hosting, accounts, AI, Blender sidebar integration and complete Blender coverage. Omitting merge is a product choice: uncertain identity should not silently authorize writes.
