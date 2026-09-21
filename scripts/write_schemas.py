"""Reproducibly write language-neutral v1 contract schemas."""

import json
from pathlib import Path


def obj(properties, required):
    return {"type": "object", "properties": properties, "required": required}


string = {"type": "string"}
strings = {"type": "array", "items": string}
source = obj(
    {"name": string, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}},
    ["name", "sha256"],
)
coverage = obj(
    {"compared": strings, "not_compared": strings}, ["compared", "not_compared"]
)
property_schema = obj(
    {"value": {}, "category": string, "label": string, "coverage": string},
    ["value", "category", "label", "coverage"],
)
entity = obj(
    {
        "id": string,
        "type": string,
        "name": string,
        "properties": {"type": "object", "additionalProperties": property_schema},
        "relations": {"type": "object", "additionalProperties": strings},
        "identity": {"type": "object"},
        "spatial": {"type": "object"},
        "visual": {"type": "object"},
        "extensions": {"type": "object"},
    },
    ["id", "type", "name", "properties", "relations", "identity"],
)
snapshot = obj(
    {
        "schema_version": {"const": "1.0"},
        "adapter": obj({"name": string, "version": string}, ["name", "version"]),
        "application": {"type": "object"},
        "source": source,
        "context": {"type": "object"},
        "coverage": coverage,
        "entities": {"type": "array", "items": entity},
    },
    ["schema_version", "adapter", "source", "coverage", "entities"],
)
change = obj(
    {
        "category": string,
        "label": string,
        "domain": {"enum": ["authored", "evaluated"]},
        "before": {},
        "after": {},
        "compatible": {"type": "boolean"},
        "displacement": {"type": "object"},
    },
    ["category", "label", "domain", "before", "after"],
)
record = obj(
    {
        "id": string,
        "name": string,
        "type": string,
        "status": {"enum": ["added", "removed", "modified", "unchanged", "ambiguous"]},
        "before": {"type": ["string", "null"]},
        "after": {"type": ["string", "null"]},
        "match": obj(
            {"confidence": string, "evidence": strings}, ["confidence", "evidence"]
        ),
        "changes": {"type": "array", "items": change},
    },
    ["id", "name", "type", "status", "before", "after", "match", "changes"],
)
pair = obj(
    {"before": string, "after": string, "evidence": strings},
    ["before", "after", "evidence"],
)
ir = obj(
    {
        "schema_version": {"const": "1.0"},
        "before": source,
        "after": source,
        "correspondences": {"type": "array", "items": pair},
        "ambiguity": {"type": "array", "items": pair},
        "records": {"type": "array", "items": record},
        "coverage": coverage,
        "summary": {
            "type": "object",
            "additionalProperties": {"type": "integer", "minimum": 0},
        },
        "context": {"type": "object"},
    },
    [
        "schema_version",
        "before",
        "after",
        "correspondences",
        "ambiguity",
        "records",
        "coverage",
        "summary",
    ],
)
for name, schema in [("snapshot", snapshot), ("change", ir)]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"Semantic Change Explorer {name} v1",
        **schema,
    }
    Path(f"schemas/{name}-1.0.schema.json").write_text(
        json.dumps(schema, indent=2) + "\n"
    )
