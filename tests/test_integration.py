"""Real Blender fixture test, opt in with SCE_INTEGRATION=1."""

import json
import os
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from semantic_change_explorer.adapters.blender import effects, extract, locate
from semantic_change_explorer.core.diff import compare
from semantic_change_explorer.core.model import dumps, fingerprint


@unittest.skipUnless(
    os.environ.get("SCE_INTEGRATION") == "1",
    "Real Blender integration: set SCE_INTEGRATION=1",
)
class BlenderTests(unittest.TestCase):
    def test_full_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(
                [
                    locate(),
                    "--background",
                    "--factory-startup",
                    "--disable-autoexec",
                    "--python-exit-code",
                    "3",
                    "--python",
                    str(Path("scripts/generate_fixture.py").resolve()),
                    "--",
                    "--output",
                    str(root),
                ],
                check=True,
                capture_output=True,
            )
            before, after = root / "before.blend", root / "after.blend"
            hashes = [fingerprint(before), fingerprint(after)]
            a, _ = extract(before, root / "a.json", root / "a.glb")
            b, _ = extract(after, root / "b.json", root / "b.glb")
            again, _ = extract(before, root / "again.json")
            self.assertEqual(dumps(a), dumps(again))
            self.assertEqual(hashes, [fingerprint(before), fingerprint(after)])
            self.assertFalse((root / "AUTOEXEC_RAN").exists())
            self.assertTrue(a["context"]["autoexec_disabled"])
            ir, _ = compare(a, b, effects)
            cats = {c["category"] for r in ir["records"] for c in r["changes"]}
            self.assertTrue(
                {
                    "moved",
                    "renamed",
                    "modifier",
                    "material",
                    "geometry",
                    "relationship",
                    "camera",
                    "light",
                    "evaluated",
                }
                <= cats,
                cats,
            )
            self.assertEqual(ir["summary"]["added"], 1)
            self.assertEqual(ir["summary"]["removed"], 1)
            self.assertEqual(ir["summary"]["ambiguous"], 4)
            # GLB JSON chunk provides the actual mapping, not a name assumption.
            data = (root / "a.glb").read_bytes()
            self.assertEqual(data[:4], b"glTF")
            length = struct.unpack_from("<I", data, 12)[0]
            glb = json.loads(data[20 : 20 + length])
            ids = {n.get("extras", {}).get("sce_entity") for n in glb["nodes"]}
            ids.discard(None)
            expected = {e["id"] for e in a["entities"] if e["type"] == "blender.mesh"}
            self.assertEqual(ids, expected)
            expected_summary = json.loads(
                Path("fixtures/expected-summary.json").read_text()
            )
            self.assertEqual(ir["summary"], expected_summary)
