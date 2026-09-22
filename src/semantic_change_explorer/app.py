"""Local GUI-first workflow: browser uploads, loopback-only processing, and report UI."""

import json
import os
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.parser import BytesParser
from email.policy import default
from io import BytesIO
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from .adapters.blender import effects, extract
from .core.diff import compare
from .core.model import write
from .report import build_report, viewer_assets


class LocalCompareServer(ThreadingHTTPServer):
    """Loopback-only local server hosting the browser workflow and job artifacts."""

    allow_reuse_address = True

    def __init__(self, server_address, directory=None, static_root=None):
        self.directory = Path(directory or Path.cwd()).resolve()
        self.static_root = Path(static_root).resolve() if static_root else None
        self.job_root = self.directory / "jobs"
        self.job_root.mkdir(parents=True, exist_ok=True)
        super().__init__(server_address, LocalCompareHandler)


class LocalCompareHandler(SimpleHTTPRequestHandler):
    _root: Path
    _static_root: Path

    def setup(self):
        self._root = Path(self.server.directory).resolve()
        self._static_root = self.server.static_root or self._root / "web" / "dist"
        if not self._static_root.exists():
            self._static_root = self._root / "web"
        super().setup()

    def log_message(self, format, *args):
        return

    def end_headers(self):
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._serve_static_file(self._static_root / "index.html")
            return

        if path.startswith("/jobs/"):
            target = self._resolve_job_path(path)
            if target is None:
                self.send_error(404)
                return
            if target.is_dir():
                status = target / "status.json"
                if status.exists():
                    try:
                        payload = json.loads(status.read_text(encoding="utf-8"))
                    except Exception:
                        payload = None
                    if payload and payload.get("state") == "processing":
                        self._serve_processing_page(target, payload)
                        return
                index = target / "index.html"
                if index.exists():
                    self._serve_static_file(index)
                    return
            if target.is_file():
                self._serve_static_file(target)
                return
            self.send_error(404)
            return

        if path.startswith("/api/"):
            self.send_error(404)
            return

        self._serve_static_file(self._static_root / path.lstrip("/"))

    def _parse_multipart_form(self):
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data"):
            raise ValueError("Expected multipart/form-data upload.")

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        message = BytesParser(policy=default).parsebytes(
            f"Content-Type: {content_type}\r\n\r\n".encode("latin1") + body
        )

        fields = {}
        for part in message.iter_parts():
            disposition = part.get("Content-Disposition", "")
            if "form-data" not in disposition.lower():
                continue
            name = part.get_param("name", header="Content-Disposition")
            if not name:
                continue
            payload = part.get_payload(decode=True)
            filename = part.get_filename()
            if filename is not None:
                fields[name] = type("UploadedFile", (), {"filename": filename, "file": BytesIO(payload or b"")})()
            else:
                fields[name] = payload.decode("utf-8") if payload is not None else ""
        return fields

    def _process_job(self, job_id, before_path, after_path):
        job_dir = self.server.job_root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        status_path = job_dir / "status.json"
        steps = [
            "loading before file",
            "extracting before scene",
            "loading after file",
            "extracting after scene",
            "matching and diffing",
            "building report",
        ]
        try:
            write(status_path, {"ok": False, "state": "processing", "job_id": job_id, "progress": 5, "step": steps[0]})
            threads_per_blender = max(1, (os.cpu_count() or 1) // 2)
            write(status_path, {"ok": False, "state": "processing", "job_id": job_id, "progress": 15, "step": "extracting both scene states"})
            jobs = {
                "before": (before_path, job_dir / "a.snapshot.json", job_dir / "a.glb"),
                "after": (after_path, job_dir / "b.snapshot.json", job_dir / "b.glb"),
            }
            extracted = {}
            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="sce-blender") as pool:
                futures = {
                    pool.submit(extract, source, snapshot, glb, None, threads_per_blender): side
                    for side, (source, snapshot, glb) in jobs.items()
                }
                for completed, future in enumerate(as_completed(futures), start=1):
                    extracted[futures[future]] = future.result()
                    write(
                        status_path,
                        {
                            "ok": False,
                            "state": "processing",
                            "job_id": job_id,
                            "progress": 40 if completed == 1 else 65,
                            "step": "one scene extracted; extracting the other"
                            if completed == 1
                            else "both scene states extracted",
                        },
                    )
            a, ta = extracted["before"]
            b, tb = extracted["after"]
            write(status_path, {"ok": False, "state": "processing", "job_id": job_id, "progress": 70, "step": steps[4]})
            ir, timings = compare(a, b, effects)
            write(status_path, {"ok": False, "state": "processing", "job_id": job_id, "progress": 80, "step": steps[5]})
            write(job_dir / "changes.json", ir)
            build_report(job_dir, a, b, ir, {"before": ta, "after": tb, **timings})
            write(status_path, {"ok": True, "state": "complete", "job_id": job_id, "progress": 100, "step": "complete"})
        except Exception as exc:
            try:
                write(status_path, {"ok": False, "state": "error", "error": str(exc), "job_id": job_id, "progress": 0, "step": "error"})
            except FileNotFoundError:
                pass
        finally:
            if before_path.exists():
                before_path.unlink(missing_ok=True)
            if after_path.exists():
                after_path.unlink(missing_ok=True)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/compare":
            self.send_error(404)
            return

        try:
            form = self._parse_multipart_form()
            before_value = form.get("before")
            after_value = form.get("after")
            if before_value is None or after_value is None:
                raise ValueError("Before and After files are required.")
            before_file = before_value
            after_file = after_value
            if before_file.filename.lower().endswith(".blend") is False:
                raise ValueError("Before file must be a .blend file.")
            if after_file.filename.lower().endswith(".blend") is False:
                raise ValueError("After file must be a .blend file.")

            job_id = uuid.uuid4().hex
            job_dir = self.server.job_root / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            before_path = job_dir / "before.blend"
            after_path = job_dir / "after.blend"
            before_path.write_bytes(before_file.file.read())
            after_path.write_bytes(after_file.file.read())

            thread = threading.Thread(
                target=self._process_job,
                args=(job_id, before_path, after_path),
                daemon=True,
            )
            thread.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            job_url = f"http://127.0.0.1:{self.server.server_port}/jobs/{job_id}/"
            self.wfile.write(
                json.dumps({"ok": True, "job_id": job_id, "job_url": job_url}).encode()
            )
        except Exception as exc:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"ok": False, "error": str(exc)}).encode()
            )

    def _resolve_job_path(self, request_path):
        normalized = request_path.rstrip("/")
        if not normalized.startswith("/jobs/"):
            return None
        cleaned = normalized.split("/jobs/", 1)[1]
        if not cleaned:
            return None
        parts = cleaned.split("/")
        job_id = parts[0]
        if not job_id:
            return None
        base = self.server.job_root / job_id
        if not base.exists():
            return None
        if len(parts) == 1:
            return base
        relative = "/".join(parts[1:])
        return base / relative

    def _serve_processing_page(self, job_dir, payload=None):
        progress = int((payload or {}).get("progress", 0))
        step = (payload or {}).get("step", "processing")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""
<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Semantic Change Explorer</title>
    <meta http-equiv=\"refresh\" content=\"2\" />
    <style>
      html, body {{ margin: 0; padding: 0; background: #07141d; color: #edf5fb; font-family: system-ui, sans-serif; }}
      body {{ min-height: 100vh; display: grid; place-items: center; }}
      .card {{ width: min(960px, 92vw); }}
      h1 {{ font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 300; margin: 0 0 1rem; }}
      p {{ font-size: clamp(1.1rem, 2vw, 1.8rem); margin: 0; color: #dfeaf5; }}
      .muted {{ color: #9bb5c8; margin-top: 1.5rem; }}
      .bar {{ height: 18px; border-radius: 999px; overflow: hidden; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.08); margin-top: 1.25rem; }}
      .fill {{ height: 100%; width: {progress}%; background: linear-gradient(90deg, #67e8f9, #a78bfa, #f9a8d4); transition: width 0.3s ease; }}
      .meta {{ margin-top: 0.75rem; color: #9bb5c8; font-size: 0.95rem; }}
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>Processing your comparison…</h1>
      <p>Working locally on the before/after scene analysis.</p>
      <div class=\"bar\"><div class=\"fill\"></div></div>
      <p class=\"meta\">Progress: {progress}% · {step}</p>
      <p class=\"muted\">This page refreshes automatically until the result is ready.</p>
    </div>
  </body>
</html>
"""
        self.wfile.write(html.encode("utf-8"))

    def _serve_static_file(self, path):
        resolved = Path(path).resolve()
        if not resolved.exists() or not resolved.is_file():
            self.send_error(404)
            return
        self.send_response(200)
        if resolved.suffix.lower() == ".html":
            self.send_header("Content-Type", "text/html; charset=utf-8")
        elif resolved.suffix.lower() == ".json":
            self.send_header("Content-Type", "application/json")
        elif resolved.suffix.lower() == ".js":
            self.send_header("Content-Type", "application/javascript")
        elif resolved.suffix.lower() == ".css":
            self.send_header("Content-Type", "text/css")
        else:
            self.send_header("Content-Type", "application/octet-stream")
        self.end_headers()
        with resolved.open("rb") as handle:
            shutil.copyfileobj(handle, self.wfile)


def main():
    parser = __import__("argparse").ArgumentParser(
        prog="sce-app",
        description="Launch the browser-first local comparison app.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    runtime_root = Path.cwd().resolve()
    server = LocalCompareServer(
        (args.host, args.port),
        directory=str(runtime_root),
        static_root=str(viewer_assets()),
    )
    print(f"http://{args.host}:{args.port}")
    if args.open:
        import webbrowser

        webbrowser.open(f"http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
