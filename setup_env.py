"""Finish setting up the Python environment.

Run this once after installing the packages in ``requirements.txt``::

    .venv\\Scripts\\python.exe setup_env.py

It tells pyqtgraph to use PySide6 (the GUI toolkit this application is built
with) and checks that the main packages can be imported. BrainFlow is bundled
in the repository's ``brainflow`` folder, so it is not installed separately.
"""
import os
import sys
import sysconfig

LINES = [
    "# Written by FreeBCI_GUI_app/setup_env.py - pins the Qt binding for pyqtgraph.\n",
    "import os\n",
    "import warnings\n",
    'os.environ["PYQTGRAPH_QT_LIB"] = "PySide6"\n',
    'os.environ["QT_API"] = "pyside6"\n',
    "# BrainFlow 4.x still imports pkg_resources, which emits a deprecation\n",
    "# warning on startup; the application does not use that API itself.\n",
    'warnings.filterwarnings("ignore", message="pkg_resources is deprecated",\n',
    '                        category=UserWarning)\n',
]


def brainflow_location():
    try:
        import brainflow
        return os.path.dirname(os.path.abspath(brainflow.__file__))
    except Exception:  # noqa: BLE001
        return None


def main(argv):
    if not (3, 10) <= sys.version_info[:2] < (3, 13):
        print('FreeBCI requires Python 3.10-3.12 x64; use a fresh migration environment.')
        return 1
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
    failed = False
    try:
        import PySide6
        checks.append("PySide6 %s ok" % PySide6.__version__)
    except Exception as exc:  # noqa: BLE001
        checks.append("PySide6 MISSING (%s)" % exc)
        failed = True
    try:
        from brainflow.board_shim import BoardShim
        rate = BoardShim.get_sampling_rate(2038)
    except Exception as exc:  # noqa: BLE001
        checks.append("brainflow MISSING (%s)" % exc)
        failed = True
    else:
        location = brainflow_location() or "?"
        checks.append("brainflow bundled at %s (native board 2038: %s Hz)" % (location, rate))
    try:
        import pyperclip  # noqa: F401
    except Exception:  # noqa: BLE001
        checks.append("pyperclip MISSING")
        failed = True
    else:
        checks.append("pyperclip ok")
    print("; ".join(checks))
    print()
    print("run the app with:")
    print('    "%s" FreeBCI_GUI.py' % sys.executable)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
