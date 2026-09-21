"""Fail release checks if public documentation or distribution contents are missing."""

import tarfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "CONTRIBUTING.md",
]
required += [
    "docs/" + n + ".md"
    for n in [
        "product-thesis",
        "competitive-audit",
        "architecture",
        "data-model",
        "entity-matching",
        "diff-semantics",
        "visual-language",
        "security",
        "testing",
        "performance",
        "dependencies",
        "contributing",
        "code-tour",
        "build-log",
        "licensing",
        "release-checklist",
    ]
]
for name in required:
    assert (root / name).is_file(), f"Missing {name}"
assert list((root / "dist").glob("*.whl")), "Build a wheel before the release audit"
assert list((root / "dist").glob("*.tar.gz")), (
    "Build a source archive before the release audit"
)
for path in (root / "dist").glob("*"):
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
        assert any(n.endswith("viewer/index.html") for n in names), "Wheel lacks viewer"
        assert any(n.endswith("licenses/three.txt") for n in names), (
            "Wheel lacks dependency notices"
        )
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path) as archive:
            names = archive.getnames()
        assert any(n.endswith("web/src/Viewer.tsx") for n in names), (
            "Source archive lacks viewer source"
        )
    else:
        continue
    assert not any("private-notes" in n for n in names), (
        "Private notes leaked into distribution"
    )
print("Required public docs and available distribution contents verified.")
