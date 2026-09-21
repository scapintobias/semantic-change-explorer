"""Actionable failures, argument handling, output protection and local serving."""

import json
import tempfile
import threading
import unittest
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from test_core import entity, snap

from semantic_change_explorer.adapters.blender import extract, locate
from semantic_change_explorer.core.model import validate
from semantic_change_explorer.report import LocalHandler

# GUI-first loopback workflow regression: this route must accept multipart payloads
# and begin the local comparison pipeline without the CLI output-directory flow.


class SafetyTests(unittest.TestCase):
    def test_bad_property_shape_is_actionable(self):
        s = snap(entity())
        s["entities"][0]["properties"] = {"bad": {"value": 1}}
        with self.assertRaisesRegex(ValueError, "Semantic property"):
            validate(s)

    def test_wrong_version_rejected(self):
        from subprocess import CompletedProcess

        with patch(
            "semantic_change_explorer.adapters.blender.subprocess.run",
            return_value=CompletedProcess([], 0, "Blender 3.6.0", ""),
        ):
            with self.assertRaisesRegex(ValueError, "Unsupported Blender"):
                locate("/example/blender")

    def test_source_output_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.blend"
            path.write_bytes(b"test")
            with self.assertRaisesRegex(ValueError, "overwrite"):
                extract(path, path)
            self.assertEqual(path.read_bytes(), b"test")

    def test_literal_subprocess_arguments(self):
        from subprocess import CompletedProcess

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "a $(not-a-command).blend"
            source.write_bytes(b"test")
            output = Path(tmp) / "snapshot.json"

            def fake_run(args, **kwargs):
                self.assertIsInstance(args, list)
                self.assertLess(
                    args.index("--disable-autoexec"), args.index(str(source.resolve()))
                )
                self.assertNotIn("shell", kwargs)
                output.write_text(json.dumps(snap(entity())))
                return CompletedProcess(args, 0, "", "")

            with (
                patch(
                    "semantic_change_explorer.adapters.blender.locate",
                    return_value="/blender",
                ),
                patch(
                    "semantic_change_explorer.adapters.blender.subprocess.run",
                    side_effect=fake_run,
                ),
            ):
                extract(source, output)

    def test_timeout_detects_source_mutation(self):
        from subprocess import TimeoutExpired

        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "a.blend"
            source.write_bytes(b"test")

            def fake_run(*args, **kwargs):
                source.write_bytes(b"concurrent edit")
                raise TimeoutExpired("blender", 300)

            with (
                patch(
                    "semantic_change_explorer.adapters.blender.locate",
                    return_value="/blender",
                ),
                patch(
                    "semantic_change_explorer.adapters.blender.subprocess.run",
                    side_effect=fake_run,
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "fingerprint changed"):
                    extract(source, Path(tmp) / "out.json")

    def test_server_denies_escape_and_sets_csp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "report"
            root.mkdir()
            (root / "index.html").write_text("report")
            secret = Path(tmp) / "secret.txt"
            secret.write_text("secret")
            (root / "escape.txt").symlink_to(secret)
            server = ThreadingHTTPServer(
                ("127.0.0.1", 0), partial(LocalHandler, directory=str(root))
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(url) as r:
                    self.assertIn(
                        "default-src 'self'", r.headers["Content-Security-Policy"]
                    )
                with self.assertRaises(HTTPError) as failure:
                    urlopen(url + "/escape.txt")
                self.assertEqual(failure.exception.code, 403)
                failure.exception.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_local_loopback_api_accepts_multipart(self):
        from semantic_change_explorer.app import LocalCompareServer
        from urllib.request import Request

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = root / "before.blend"
            after = root / "after.blend"
            before.write_bytes(b"before")
            after.write_bytes(b"after")

            server = LocalCompareServer(("127.0.0.1", 0), directory=str(root))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_port}/api/compare"
            payload = []
            payload.append(b"--boundary\r\nContent-Disposition: form-data; name=before; filename=before.blend\r\nContent-Type: application/octet-stream\r\n\r\n")
            payload.append(b"before\r\n--boundary\r\nContent-Disposition: form-data; name=after; filename=after.blend\r\nContent-Type: application/octet-stream\r\n\r\n")
            payload.append(b"after\r\n--boundary--\r\n")
            body = b"".join(payload)

            req = Request(
                url,
                method="POST",
                data=body,
                headers={"Content-Type": "multipart/form-data; boundary=boundary"},
            )
            try:
                with urlopen(req) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(b"job_url", response.read())
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
