"""Canonical JSON policy. Quantization is serialization, tolerance is comparison."""

import hashlib
import json
import math
from pathlib import Path

VERSION = "1.0"
EPSILON = 1e-5
DIGITS = 6


def canonical(value):
    """Return finite JSON data, sorted keys, floats quantized to six decimals."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite numeric value in snapshot")
        return round(value, DIGITS) or 0.0
    if isinstance(value, dict):
        return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    return value


def dumps(value):
    """Deterministic UTF-8 JSON; sequence ordering remains semantically significant."""
    return (
        json.dumps(
            canonical(value),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )


def write(path, value):
    """Write canonical UTF-8 JSON to a caller-owned output path."""
    Path(path).write_text(dumps(value), encoding="utf-8")


def fingerprint(path):
    """Hash file bytes incrementally without loading the entire input into memory."""
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def equivalent(a, b):
    """Absolute tolerance in native units; booleans are never treated as numbers."""
    if type(a) is bool or type(b) is bool:
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=0, abs_tol=EPSILON)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equivalent(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equivalent(x, y) for x, y in zip(a, b))
    return a == b


def validate(snapshot):
    """Validate core invariants before matching untrusted snapshot input."""
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != VERSION:
        raise ValueError(
            "Unsupported snapshot schema; expected 1.0. Re-extract both inputs."
        )
    for key in ("adapter", "source", "coverage", "entities"):
        if key not in snapshot:
            raise ValueError(f"Snapshot missing {key}")
    if not isinstance(snapshot["entities"], list):
        raise ValueError("Snapshot entities must be an array")
    for group, keys in (
        ("adapter", ("name", "version")),
        ("source", ("name", "sha256")),
        ("coverage", ("compared", "not_compared")),
    ):
        if not isinstance(snapshot[group], dict) or any(
            k not in snapshot[group] for k in keys
        ):
            raise ValueError(f"Invalid snapshot {group}")
    if any(
        not isinstance(snapshot["coverage"][key], list)
        or any(not isinstance(x, str) for x in snapshot["coverage"][key])
        for key in ("compared", "not_compared")
    ):
        raise ValueError("Coverage lists must contain strings")
    ids = set()
    for entity in snapshot["entities"]:
        if not isinstance(entity, dict):
            raise ValueError("Every entity must be an object")
        for key in ("id", "type", "name", "properties", "relations", "identity"):
            if key not in entity:
                raise ValueError(f"Entity missing {key}")
        if any(not isinstance(entity[k], str) for k in ("id", "type", "name")):
            raise ValueError("Entity id, type and name must be strings")
        if entity["id"] in ids:
            raise ValueError("Snapshot entity identifiers must be unique strings")
        ids.add(entity["id"])
        if any(
            not isinstance(entity[k], dict)
            for k in ("properties", "relations", "identity")
        ):
            raise ValueError(
                "Entity properties, relations and identity must be objects"
            )
        for prop in entity["properties"].values():
            if not isinstance(prop, dict) or any(
                k not in prop for k in ("value", "category", "label", "coverage")
            ):
                raise ValueError(
                    "Semantic property missing value/category/label/coverage"
                )
            if any(
                not isinstance(prop[k], str) for k in ("category", "label", "coverage")
            ):
                raise ValueError("Semantic property descriptors must be strings")
    for entity in snapshot["entities"]:
        for targets in entity["relations"].values():
            if not isinstance(targets, list) or any(
                not isinstance(t, str) or t not in ids for t in targets
            ):
                raise ValueError("Relationship references unknown entity")
    canonical(snapshot)
    return snapshot


def read(path):
    """Decode and validate a snapshot file before comparison."""
    return validate(json.loads(Path(path).read_text(encoding="utf-8")))
