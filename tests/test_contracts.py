"""Golden examples and published schema validation (jsonschema is dev-only)."""

import json
import unittest
from pathlib import Path

from semantic_change_explorer.adapters.blender import effects
from semantic_change_explorer.core.diff import compare
from semantic_change_explorer.core.model import canonical, read

try:
    import jsonschema
except ImportError:
    jsonschema = None


class ContractTests(unittest.TestCase):
    def test_golden_ir(self):
        actual, _ = compare(
            read("fixtures/before.snapshot.json"),
            read("fixtures/after.snapshot.json"),
            effects,
        )
        expected = json.loads(Path("fixtures/expected-change.json").read_text())
        self.assertEqual(canonical(actual), expected)

    @unittest.skipUnless(
        jsonschema, "Install jsonschema to validate published contracts"
    )
    def test_schemas(self):
        for name, files in [
            ("snapshot", ["before.snapshot", "after.snapshot"]),
            ("change", ["expected-change"]),
        ]:
            schema = json.loads(Path(f"schemas/{name}-1.0.schema.json").read_text())
            for file in files:
                jsonschema.validate(
                    json.loads(Path(f"fixtures/{file}.json").read_text()), schema
                )
