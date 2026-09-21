"""Conservative mutual-best matcher; quadratic candidates, no forced assignment.

Scores rank evidence, not probability. A source and target must each prefer the
other by a margin. Ties remain unresolved. No persistent identity is inferred
from a snapshot-local identifier or from a name alone.
"""

from .model import equivalent

WEIGHTS = {"geometry": 6, "topology": 2, "data": 2, "context": 1, "materials": 1}
THRESHOLD = 5
MARGIN = 2


def evidence(a, b):
    """Score compatible entities using adapter-provided identity hints."""
    if a["type"] != b["type"]:
        return 0, []
    score, reasons = 0, []
    if a["name"] == b["name"]:
        score += 4
        reasons.append("same name (not proof of identity)")
    for key, weight in WEIGHTS.items():
        av, bv = a["identity"].get(key), b["identity"].get(key)
        if av not in (None, "", [], {}) and av == bv:
            score += weight
            reasons.append(f"same {key}")
    if a.get("spatial") and equivalent(a["spatial"], b.get("spatial")):
        score += 1
        reasons.append("same spatial transform")
    return score, reasons


def match(before, after):
    """Return one-to-one inferred pairs plus unresolved candidates.

    O(A*B) candidate storage; each acceptance round is linear in candidates.
    Worst case O(min(A,B)*A*B) time. Matching is deliberately partial: this implementation
    does not solve a maximum-weight global assignment that would force ties.
    """
    left = sorted(before["entities"], key=lambda e: e["id"])
    right = sorted(after["entities"], key=lambda e: e["id"])
    # Equal captured state of the same fingerprinted artifact needs no heuristic.
    # This does not assert persistent identity across independently saved files.
    if before["source"] == after["source"] and left == right:
        return [
            {
                "before": entity["id"],
                "after": entity["id"],
                "confidence": "exact state",
                "method": "identical-source-observation",
                "evidence": [
                    "same source fingerprint and identical captured entity state"
                ],
            }
            for entity in left
        ], []
    candidates = []
    for a in left:
        for b in right:
            score, reasons = evidence(a, b)
            if score >= THRESHOLD:
                candidates.append(
                    {
                        "before": a["id"],
                        "after": b["id"],
                        "score": score,
                        "evidence": reasons,
                    }
                )
    pairs, used_a, used_b = [], set(), set()
    # Recompute mutual preferences after confident pairs are removed.
    while True:
        remaining = [
            c
            for c in candidates
            if c["before"] not in used_a and c["after"] not in used_b
        ]
        ranks_a, ranks_b = {}, {}
        for c in remaining:
            for ranks, key in ((ranks_a, "before"), (ranks_b, "after")):
                ranks[c[key]] = sorted(
                    ranks.get(c[key], []) + [c["score"]], reverse=True
                )[:2]
        accepted = []
        for c in remaining:

            def unique_best(ranks, key):
                scores = ranks[c[key]]
                return (
                    c["score"] == scores[0]
                    and c["score"] - (scores[1] if len(scores) > 1 else 0) >= MARGIN
                )

            if unique_best(ranks_a, "before") and unique_best(ranks_b, "after"):
                accepted.append(c)
        if not accepted:
            break
        for c in accepted:
            a = next(e for e in left if e["id"] == c["before"])
            b = next(e for e in right if e["id"] == c["after"])
            exact = (
                before["source"].get("sha256")
                and before["source"] == after["source"]
                and a == b
            )
            confidence = (
                "exact state"
                if exact
                else (
                    "strong inferred" if a["name"] == b["name"] else "probable rename"
                )
            )
            pairs.append(
                {k: v for k, v in c.items() if k != "score"}
                | {"confidence": confidence, "method": "mutual-best-margin"}
            )
            used_a.add(c["before"])
            used_b.add(c["after"])
    unresolved = [
        c for c in candidates if c["before"] not in used_a and c["after"] not in used_b
    ]
    return pairs, [{k: v for k, v in c.items() if k != "score"} for c in unresolved]
