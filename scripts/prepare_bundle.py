"""Collect available notices and path-free inventory, not legal clearance."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "release-metadata"


def main():
    licenses = OUT / "licenses"
    licenses.mkdir(parents=True, exist_ok=True)
    distributions = []
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata["Name"].lower()):
        name = re.sub(r"[^a-zA-Z0-9_.-]", "_", dist.metadata["Name"])
        copied = []
        for entry in dist.files or []:
            if re.match(r"(?i)^(license|licence|copying|notice|copyright)", Path(str(entry)).name):
                source = Path(dist.locate_file(entry))
                if not source.is_file():
                    continue
                relative = Path(*[p for p in entry.parts if p not in ("..", ".")])
                target = licenses / name / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                copied.append(target.relative_to(OUT).as_posix())
        distributions.append({"name": name, "version": dist.version, "license_files": copied})
    python_root = Path(sys.base_prefix)
    shutil.copy2(python_root / "LICENSE.txt", licenses / "Python-LICENSE.txt")
    for source in (python_root / "tcl").rglob("license.terms"):
        target = licenses / "Tcl-Tk" / source.relative_to(python_root / "tcl")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    tools = []
    for name, flag in [("ffmpeg", "-version"), ("ffprobe", "-version"), ("deno", "--version")]:
        source = ROOT / "tools" / (name + ".exe")
        result = subprocess.run([str(source), flag], capture_output=True, text=True,
                                encoding="utf-8", check=True, timeout=30)
        with source.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        tools.append({"file": "tools/" + source.name, "sha256": digest,
                      "version": result.stdout.splitlines()[0]})
    manifest = {"app_version": "1.0.0", "python": sys.version.split()[0],
                "platform": "Windows x64", "packages": distributions, "tools": tools,
                "publication_ready": False,
                "gate": "Verify corresponding sources and all third-party notices before publishing."}
    (OUT / "BUILD-INVENTORY.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Collected inventory: {len(distributions)} distributions, {len(tools)} tools.")


if __name__ == "__main__":
    main()
