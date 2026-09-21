"""Stage built viewer and dependency licenses into the Python wheel package."""

import shutil
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
subprocess.run(["npm", "run", "build", "--prefix", str(root / "web")], check=True)
target = root / "src/semantic_change_explorer/viewer"
# Only overwrite this generated assets folder; source is web/src.
if target.exists():
    shutil.rmtree(target)
shutil.copytree(root / "web/dist", target)
licenses = target / "licenses"
licenses.mkdir()
for package in ("react", "react-dom", "scheduler", "three"):
    source = root / "web/node_modules" / package / "LICENSE"
    if not source.exists():
        source = source.with_name("LICENSE.md")
    shutil.copyfile(source, licenses / (package + ".txt"))
shutil.copyfile(root / "LICENSE", licenses / "project-GPL-3.0.txt")
