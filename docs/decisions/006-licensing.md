# GPL-3.0-or-later for project code

Status: accepted for v0.1 — 2026-09-21.

## Context
The Blender extractor uses bpy; published Blender scripts have GPL obligations according to Blender Foundation guidance.

## Decision
License the complete initial codebase GPL-3.0-or-later; preserve MIT notices for bundled web dependencies.

## Alternatives
Split permissive core/GPL adapter now; claim external process isolation automatically removes obligations.

## Consequences
Simple compatible initial distribution; no claim that the boundary settles legal questions. Source/build instructions must accompany binary distribution. See docs/licensing.md for sources.
