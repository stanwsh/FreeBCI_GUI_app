"""Build a self-contained source release zip.

The release is a folder users can unpack and run with ``setup_env.cmd``; it is
not a Python wheel.  BrainFlow is intentionally bundled under ``brainflow/`` and
is never installed from PyPI.

Usage:
    python tools/build_release.py --version 0.1.4
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from freebci.version import VERSION  # noqa: E402

REQUIRED_FILES = (
    "FreeBCI_GUI.py",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "run.cmd",
    "setup_env.cmd",
    "setup_env.py",
    "uv.lock",
    "electrodes_pos_32.png",
    "electrodes_pos_64.png",
)
REQUIRED_DIRS = ("freebci", "brainflow", "settings", "docs", "examples")
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    ".uv-cache",
    ".uv-python",
    ".test-tmp",
    "logs",
    "dist",
    "__pycache__",
    ".pytest_cache",
}


def add_file(archive: zipfile.ZipFile, path: str) -> int:
    relative = os.path.relpath(path, REPO_ROOT)
    if relative.startswith(".."):
        raise ValueError("refusing to package a file outside the repository: %s" % path)
    archive.write(path, relative.replace(os.sep, "/"))
    return os.path.getsize(path)


def build(version: str, output: str) -> dict:
    for name in REQUIRED_FILES:
        if not os.path.isfile(os.path.join(REPO_ROOT, name)):
            raise FileNotFoundError("release is missing %s" % name)
    for name in REQUIRED_DIRS:
        if not os.path.isdir(os.path.join(REPO_ROOT, name)):
            raise FileNotFoundError("release is missing %s/" % name)

    output = os.path.abspath(output)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    if os.path.exists(output):
        os.remove(output)

    count = 0
    total = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in REQUIRED_FILES:
            total += add_file(archive, os.path.join(REPO_ROOT, name))
            count += 1
        for name in REQUIRED_DIRS:
            root = os.path.join(REPO_ROOT, name)
            for base, dirs, files in os.walk(root):
                dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
                for filename in sorted(files):
                    if filename.endswith((".pyc", ".pyo")):
                        continue
                    total += add_file(archive, os.path.join(base, filename))
                    count += 1

        archive.writestr(
            "RELEASE.txt",
            "FreeBCI GUI %s\nBuilt from %s\n"
            % (version, os.path.basename(REPO_ROOT)),
        )
        count += 1

    digest = hashlib.sha256()
    with open(output, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    checksum = output + ".sha256"
    with open(checksum, "w", encoding="ascii") as handle:
        handle.write("%s  %s\n" % (digest.hexdigest(), os.path.basename(output)))

    return {
        "archive": output,
        "checksum": checksum,
        "files": count,
        "bytes": total,
        "sha256": digest.hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=VERSION)
    parser.add_argument(
        "--output",
        default=None,
        help="archive path (default: dist/FreeBCI_GUI-<version>.zip)",
    )
    args = parser.parse_args()
    output = args.output or os.path.join(
        REPO_ROOT, "dist", "FreeBCI_GUI-%s.zip" % args.version
    )
    result = build(args.version, output)
    print("Release:  %s" % result["archive"])
    print("Checksum: %s" % result["checksum"])
    print("Files:    %d" % result["files"])
    print("Size:     %.1f MB" % (result["bytes"] / (1024.0 * 1024.0)))
    print("SHA-256:  %s" % result["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
