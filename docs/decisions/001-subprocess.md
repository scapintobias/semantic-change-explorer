# Disposable Blender process

Status: accepted for v0.1 — 2026-09-21.

## Context
Native interpretation and evaluated geometry require bpy, but most tests should run without Blender.

## Decision
Invoke background Blender once per input, with factory startup and embedded autoexec disabled. Host Python remains independent.

## Alternatives
Link host to bpy; implement a binary parser; persistent Blender service.

## Consequences
Startup overhead and a separately installed executable; clean lifetime and no source-save path. This is not a security sandbox.
