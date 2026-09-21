# Exclude history and merge

Status: accepted for v0.1 — 2026-09-21.

## Context
Existing products already cover Blender snapshots and merging; uncertain identity makes writes risky.

## Decision
Focus v0.1 on arbitrary A/B inspection with no source mutations, history or merge.

## Alternatives
Build a general VCS; duplicate Blender sidebar workflows; add automatic merge for feature parity.

## Consequences
Users bring their own files/version storage. The product can inform a decision but does not apply it. Three-way inspection may be explored later; merge is explicitly not planned for this release.
