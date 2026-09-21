"""Pure comparison contracts; no Blender installation required."""

import copy
import json
import unittest

from semantic_change_explorer.adapters.blender import effects
from semantic_change_explorer.core.diff import compare
from semantic_change_explorer.core.matching import match
from semantic_change_explorer.core.model import dumps, equivalent, validate


def entity(id="a", name="Body", geometry="abc", context="Assembly"):
    return {
        "id": id,
        "name": name,
        "type": "test.part",
        "identity": {"geometry": geometry, "context": context},
        "relations": {},
        "properties": {},
        "extensions": {},
    }


def snap(*entities):
    return {
        "schema_version": "1.0",
        "adapter": {"name": "test", "version": "1"},
        "source": {"name": "test", "sha256": "0" * 64},
        "coverage": {
            "compared": [
                "structure",
                "transforms",
                "materials",
                "modifiers",
                "mesh",
                "evaluated",
            ],
            "not_compared": ["animation"],
        },
        "entities": list(entities),
    }


def prop(value, category="moved", coverage="transforms"):
    return {
        "label": "Example property",
        "value": value,
        "category": category,
        "coverage": coverage,
    }


class CoreTests(unittest.TestCase):
    def test_canonical_order_and_numeric_policy(self):
        self.assertEqual(
            dumps({"b": -0.0, "a": 1.00000001}), dumps({"a": 1.0, "b": 0.0})
        )
        self.assertTrue(equivalent(1, 1.000009))
        self.assertFalse(equivalent(1, 1.000011))
        self.assertFalse(equivalent(True, 1))
        with self.assertRaises(ValueError):
            dumps(float("nan"))

    def test_schema_and_duplicate_rejection(self):
        with self.assertRaises(ValueError):
            validate({"schema_version": "9"})
        with self.assertRaises(ValueError):
            validate(snap(entity(), entity()))
        e = entity()
        e["relations"] = {"parent": ["absent"]}
        with self.assertRaises(ValueError):
            validate(snap(e))

    def test_round_trip(self):
        a = snap(entity())
        self.assertEqual(validate(json.loads(dumps(a))), a)

    def test_identical_state_fast_path_requires_no_heuristic_hints(self):
        a = entity(geometry=None, context=None)
        pairs, uncertain = match(snap(a), snap(copy.deepcopy(a)))
        self.assertEqual(pairs[0]["method"], "identical-source-observation")
        self.assertEqual(pairs[0]["confidence"], "exact state")
        self.assertEqual(uncertain, [])

    def test_name_alone_is_not_identity(self):
        a = entity(geometry=None, context=None)
        b = entity("b", geometry=None, context=None)
        self.assertEqual(match(snap(a), snap(b))[0], [])

    def test_rename_and_move(self):
        a = entity()
        b = entity("b", "Housing")
        a["properties"]["x"] = prop(0)
        b["properties"]["x"] = prop(1)
        ir, _ = compare(snap(a), snap(b))
        self.assertEqual(ir["correspondences"][0]["confidence"], "probable rename")
        self.assertEqual(
            {c["category"] for c in ir["records"][0]["changes"]}, {"renamed", "moved"}
        )

    def test_same_name_moved(self):
        a = entity()
        b = copy.deepcopy(a)
        b["properties"]["x"] = prop(2)
        ir, _ = compare(snap(a), snap(b))
        self.assertEqual(ir["summary"]["modified"], 1)

    def test_unrelated_add_remove(self):
        ir, _ = compare(snap(entity()), snap(entity("b", "Other", "xyz", "Elsewhere")))
        self.assertEqual(ir["summary"]["added"], 1)
        self.assertEqual(ir["summary"]["removed"], 1)

    def test_duplicate_ambiguity_and_one_to_one(self):
        a = snap(entity("a", "A"), entity("b", "B"))
        b = snap(entity("x", "X"), entity("y", "Y"))
        ir, _ = compare(a, b)
        self.assertEqual(len(ir["ambiguity"]), 4)
        self.assertEqual(ir["summary"]["ambiguous"], 4)
        self.assertEqual(ir["correspondences"], [])

    def test_shared_mesh_names_anchor_correspondence(self):
        a = snap(entity("a", "A"), entity("b", "B"))
        b = snap(entity("x", "A"), entity("y", "B"))
        pairs, _ = match(a, b)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(len({p["after"] for p in pairs}), 2)

    def test_parent_rename_is_not_reparenting(self):
        a, c = entity("a", "Parent"), entity("c", "Child", "def")
        c["relations"] = {"parent": ["a"]}
        b, d = entity("b", "Renamed"), entity("d", "Child", "def")
        d["relations"] = {"parent": ["b"]}
        ir, _ = compare(snap(a, c), snap(b, d))
        child = next(r for r in ir["records"] if r["name"] == "Child")
        self.assertEqual(child["changes"], [])

    def test_relationship_and_material_modifier_classification(self):
        a, c = entity(), entity("c", "Parent", "def")
        b = copy.deepcopy(a)
        b["relations"] = {"parent": ["c"]}
        b["properties"] = {
            "mat": prop("red", "material", "materials"),
            "bevel": prop(0.3, "modifier", "modifiers"),
        }
        ir, _ = compare(snap(a, c), snap(b, c))
        r = next(r for r in ir["records"] if r["name"] == "Body")
        self.assertEqual(
            {c["category"] for c in r["changes"]},
            {"material", "modifier", "relationship"},
        )

    def test_not_compared_is_not_unchanged(self):
        a = snap(entity())
        b = copy.deepcopy(a)
        b["coverage"]["compared"].remove("materials")
        b["entities"][0]["properties"]["mat"] = prop("red", "material", "materials")
        ir, _ = compare(a, b)
        self.assertIn("materials", ir["coverage"]["not_compared"])
        self.assertEqual(ir["records"][0]["changes"], [])

    def test_geometry_compatible_displacement(self):
        mesh = {
            "vertices": [[0, 0, 0]],
            "topology": "t",
            "bounds": [[0, 0, 0], [0, 0, 0]],
            "vertex_count": 1,
            "edge_count": 0,
            "face_count": 0,
        }
        a, b = entity(), entity()
        a["extensions"] = {"blender": {"mesh": mesh}}
        b = copy.deepcopy(a)
        b["extensions"]["blender"]["mesh"]["vertices"] = [[0.1, 0, 0]]
        changes = effects(a, b, ["mesh"])
        self.assertEqual(changes[0]["displacement"]["changed_vertices"], 1)
        b["extensions"]["blender"]["mesh"]["topology"] = "other"
        self.assertFalse(effects(a, b, ["mesh"])[0]["compatible"])

    def test_deterministic_without_mutation(self):
        a, b = snap(entity()), snap(entity("b", "Housing"))
        original = dumps(a)
        self.assertEqual(dumps(compare(a, b)[0]), dumps(compare(a, b)[0]))
        self.assertEqual(dumps(a), original)

    def test_generic_entity_without_spatial_or_blender(self):
        a = entity()
        a["type"] = "document.section"
        ir, _ = compare(snap(a), snap(copy.deepcopy(a)))
        self.assertEqual(ir["summary"]["unchanged"], 1)


if __name__ == "__main__":
    unittest.main()
