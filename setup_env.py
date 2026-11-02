"""Finish setting up the Python environment.

Run this once after installing the packages in ``requirements.txt``::

    .venv\\Scripts\\python.exe setup_env.py

It tells pyqtgraph to use PyQt5 (the GUI toolkit this application is built
with) and checks that the main packages can be imported.
"""
import os
import sys
import sysconfig

LINES = [
    "# Written by FreeBCI_GUI_app/setup_env.py - pins the Qt binding for pyqtgraph.\n",
    "import os\n",
    "import warnings\n",
    'os.environ.setdefault("PYQTGRAPH_QT_LIB", "PyQt5")\n',
    "# BrainFlow 4.x still imports pkg_resources, which emits a deprecation\n",
    "# warning on startup; the application does not use that API itself.\n",
    'warnings.filterwarnings("ignore", message="pkg_resources is deprecated",\n',
    '                        category=UserWarning)\n',
]


def brainflow_version():
    try:
        import importlib.metadata as metadata
        return metadata.version("brainflow")
    except Exception:  # noqa: BLE001
        return None


def main(argv):
    site_packages = sysconfig.get_paths()["purelib"]
    target = os.path.join(site_packages, "sitecustomize.py")
    body = "".join(LINES)

    if os.path.exists(target):
        with open(target, encoding="utf-8") as fh:
            existing = fh.read()
        if existing != body:
            backup = target + ".freebci-backup"
            os.replace(target, backup)
            print("kept the previous sitecustomize as %s" % backup)

    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("wrote %s" % target)

    checks = []
    try:
        import PyQt5  # noqa: F401
        checks.append("PyQt5 ok")
    except Exception as exc:  # noqa: BLE001
        checks.append("PyQt5 MISSING (%s)" % exc)
    try:
        import brainflow  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        checks.append("brainflow MISSING (%s)" % exc)
    else:
        checks.append("brainflow %s" % (brainflow_version() or "?"))
    try:
        import pyperclip  # noqa: F401
    except Exception:  # noqa: BLE001
        checks.append("pyperclip MISSING")
    else:
        checks.append("pyperclip ok")
    print("; ".join(checks))
    print()
    print("run the app with:")
    print('    .venv\\Scripts\\python.exe FreeBCI_GUI.py')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
