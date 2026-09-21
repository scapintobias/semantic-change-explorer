"""Adapter-neutral Change IR construction, with optional domain effects hook."""

import time

from .matching import match
from .model import VERSION, equivalent, validate


def compare(before, after, effects=None):
    """Compare validated snapshots without mutating either; return IR and timings."""
    validate(before)
    validate(after)
    if before["adapter"] != after["adapter"]:
        raise ValueError("Adapter/version mismatch; re-extract with the same adapter")
    start = time.perf_counter()
    pairs, ambiguous = match(before, after)
    matched_at = time.perf_counter()
    aa = {e["id"]: e for e in before["entities"]}
    bb = {e["id"]: e for e in after["entities"]}
    mapping = {p["before"]: p["after"] for p in pairs}
    inverse = set(mapping.values())
    uncertain_a = {c["before"] for c in ambiguous}
    uncertain_b = {c["after"] for c in ambiguous}
    common = sorted(
        set(before["coverage"]["compared"]) & set(after["coverage"]["compared"])
    )
    missing = sorted(
        (set(before["coverage"]["compared"]) | set(after["coverage"]["compared"]))
        - set(common)
    )
    records = []
    for p in pairs:
        a, b = aa[p["before"]], bb[p["after"]]
        changes = []

        def add(category, label, av, bv, domain="authored"):
            if not equivalent(av, bv):
                changes.append(
                    {
                        "category": category,
                        "label": label,
                        "before": av,
                        "after": bv,
                        "domain": domain,
                    }
                )

        add("renamed", "Name differs; correspondence inferred", a["name"], b["name"])
        for key in sorted(set(a["properties"]) | set(b["properties"])):
            av, bv = a["properties"].get(key), b["properties"].get(key)
            spec = bv or av
            if spec["coverage"] in common:
                add(
                    spec["category"],
                    spec["label"],
                    av["value"] if av else None,
                    bv["value"] if bv else None,
                )
        for rel in sorted(set(a["relations"]) | set(b["relations"])):
            old = a["relations"].get(rel, [])
            new = b["relations"].get(rel, [])
            normalized = sorted(mapping.get(x, "unmatched-A:" + x) for x in old)
            if normalized != sorted(new) and "structure" in common:
                changes.append(
                    {
                        "category": "relationship",
                        "label": rel,
                        "before": [aa[x]["name"] for x in old],
                        "after": [bb[x]["name"] for x in new],
                        "before_refs": old,
                        "after_refs": new,
                        "domain": "authored",
                    }
                )
        if effects:
            changes.extend(effects(a, b, common))
        records.append(
            {
                "id": "pair:" + a["id"],
                "before": a["id"],
                "after": b["id"],
                "name": b["name"],
                "type": b["type"],
                "status": "modified" if changes else "unchanged",
                "match": p,
                "changes": changes,
            }
        )
    for side, entities, claimed, uncertain in (
        ("before", aa, set(mapping), uncertain_a),
        ("after", bb, inverse, uncertain_b),
    ):
        for ident in sorted(set(entities) - claimed):
            status = (
                "ambiguous"
                if ident in uncertain
                else ("removed" if side == "before" else "added")
            )
            records.append(
                {
                    "id": side + ":" + ident,
                    "before": ident if side == "before" else None,
                    "after": ident if side == "after" else None,
                    "name": entities[ident]["name"],
                    "type": entities[ident]["type"],
                    "status": status,
                    "match": {
                        "confidence": "ambiguous"
                        if ident in uncertain
                        else "unmatched",
                        "evidence": [],
                    },
                    "changes": [],
                }
            )
    records.sort(key=lambda r: (r["name"], r["id"]))
    not_compared = sorted(
        set(
            before["coverage"]["not_compared"]
            + after["coverage"]["not_compared"]
            + missing
        )
    )
    ir = {
        "schema_version": VERSION,
        "before": before["source"],
        "after": after["source"],
        "correspondences": pairs,
        "ambiguity": ambiguous,
        "records": records,
        "coverage": {"compared": common, "not_compared": not_compared},
        "context": {
            "before": before.get("context", {}),
            "after": after.get("context", {}),
        },
        "summary": {
            s: sum(r["status"] == s for r in records)
            for s in ("added", "removed", "modified", "unchanged", "ambiguous")
        },
    }
    return ir, {
        "matching_seconds": matched_at - start,
        "diff_seconds": time.perf_counter() - matched_at,
    }
