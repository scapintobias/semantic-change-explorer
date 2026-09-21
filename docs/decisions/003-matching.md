# Partial mutual-best matching

Status: accepted for v0.1 — 2026-09-21.

## Context
Arbitrary input files lack our own durable IDs; repeated meshes create ambiguity.

## Decision
Use transparent weights, minimum evidence, reciprocal preference and margin. Preserve unresolved candidate edges.

## Alternatives
Name equality; nearest neighbor; Hungarian global assignment; persistent IDs requiring prior instrumentation.

## Consequences
Some genuine pairs remain unmatched. Scores are uncalibrated rankings. One-to-one acceptance is deterministic; worst-case cubic work remains a scale limit.
