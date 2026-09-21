"""Portable static report writer and loopback-only restricted file server."""

import shutil
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .core.model import write


def viewer_assets():
    packaged = Path(__file__).parent / "viewer"
    dev = Path(__file__).resolve().parents[2] / "web" / "dist"
    for path in (packaged, dev):
        if (path / "index.html").is_file():
            return path
    raise ValueError(
        "Viewer assets missing. Run npm ci --prefix web && npm run build --prefix web."
    )


def build_report(output, before, after, ir, timings):
    """Copy bundled local assets; JSON is data, never injected into HTML."""
    shutil.copytree(viewer_assets(), output, dirs_exist_ok=True)
    write(Path(output) / "report.json", {"before": before, "after": after, "diff": ir})
    write(Path(output) / "timings.json", timings)


class LocalHandler(SimpleHTTPRequestHandler):
    """Reject symlink escape and directory listings; serve only the chosen root."""

    def send_head(self):
        root = Path(self.directory).resolve()
        target = Path(self.translate_path(self.path)).resolve()
        if not target.is_relative_to(root) or (
            target.is_dir() and not (target / "index.html").exists()
        ):
            self.send_error(403)
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def serve(directory, port=8765, open_browser=False):
    """Serve a report over loopback; Ctrl-C stops the read-only server."""
    root = Path(directory).resolve()
    for name in ("index.html", "report.json", "a.glb", "b.glb"):
        if not (root / name).is_file():
            raise ValueError(f"Report missing {name}; regenerate with sce compare")
    server = ThreadingHTTPServer(
        ("127.0.0.1", port), partial(LocalHandler, directory=str(root))
    )
    url = f"http://127.0.0.1:{server.server_port}"
    print(url, flush=True)
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
