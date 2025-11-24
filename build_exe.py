"""
Build script to create a Windows executable for ImageTiler using PyInstaller.

Usage (from an activated virtual environment):
    python build_exe.py                   # uses DEFAULT_BUNDLE_MODE below if no flags given
    python build_exe.py --onefile         # single large EXE
    python build_exe.py --onedir          # folder build with _internal dir (easier to debug)
    python build_exe.py --no-window       # console app (for debugging stdout/stderr)
    python build_exe.py --icon first.ico  # include an .ico file if present
    python build_exe.py --name ImageTiler # customize output name

Notes:
 - Ensure the app runs:  python main.py
 - If you edited first.ui, regenerate gui.py first:
       pyside6-uic first.ui -o gui.py
 - Requires:  pip install pyinstaller

GLOBAL SWITCH:
 - Change DEFAULT_BUNDLE_MODE = "onefile" | "onedir" below to set your preferred default.
   Command line flags still override the default when provided.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Global default for bundle mode when no CLI flag is provided.
# Set to "onefile" for a single large EXE, or "onedir" for a folder layout.
DEFAULT_BUNDLE_MODE = "onedir"

# Determine PyInstaller version capabilities at runtime
try:
    from PyInstaller import __version__ as PI_VERSION  # type: ignore
except Exception:
    PI_VERSION = "0"
try:
    from packaging.version import parse as vparse
except Exception:
    # Fallback simple parser if packaging is unavailable (shouldn't happen, but be safe)
    def vparse(s: str):  # type: ignore
        try:
            return tuple(int(x) for x in (s.split("+")[0]).split(".")[:3])
        except Exception:
            return (0,)


def ensure_in_project_root():
    here = Path(__file__).resolve().parent
    os.chdir(here)


def main(argv: list[str] | None = None) -> int:
    try:
        import PyInstaller.__main__  # type: ignore
    except Exception as e:
        print("ERROR: PyInstaller is not installed in this environment.")
        print("Install it with:  pip install pyinstaller")
        print(f"Details: {e}")
        return 1

    parser = argparse.ArgumentParser(description="Build ImageTiler executable with PyInstaller")
    parser.add_argument("entry", nargs="?", default="main.py", help="Entry-point script (default: main.py)")
    parser.add_argument("--name", default="ImageTiler", help="Output executable name")
    bundle_group = parser.add_mutually_exclusive_group()
    bundle_group.add_argument("--onefile", dest="onefile", action="store_true", help="Bundle into a single EXE")
    bundle_group.add_argument("--onedir", dest="onedir", action="store_true", help="Bundle into a folder")
    parser.add_argument("--window", dest="windowed", action="store_true", help="Windowed app (no console)")
    parser.add_argument("--no-window", dest="windowed", action="store_false", help="Console app (shows console window)")
    parser.set_defaults(windowed=True)
    parser.add_argument("--icon", default=None, help="Path to .ico file (optional)")
    parser.add_argument("--clean", action="store_true", help="Clean PyInstaller cache and remove temporary files before building")
    parser.add_argument("--noconfirm", action="store_true", help="Replace output directory without asking for confirmation")
    parser.add_argument("--collect-cv2", action="store_true", help="Force collect-all for cv2 (OpenCV) DLLs (recommended on Windows)")
    parser.add_argument("--no-collect-cv2", dest="collect_cv2", action="store_false", help="Disable cv2 collection override")
    parser.set_defaults(collect_cv2=True)
    parser.add_argument("--spec", default=None, help="Use an existing .spec file instead of CLI options")

    args = parser.parse_args(argv)

    entry = Path(args.entry)
    if not entry.exists():
        print(f"ERROR: Entry script not found: {entry}")
        return 1

    pyinstaller_args: list[str] = []

    if args.spec:
        # Build using an existing spec file
        spec_path = Path(args.spec)
        if not spec_path.exists():
            print(f"ERROR: Spec file not found: {spec_path}")
            return 1
        if args.clean:
            pyinstaller_args.append("--clean")
        if args.noconfirm:
            pyinstaller_args.append("--noconfirm")
        pyinstaller_args.append(str(spec_path))
    else:
        # Build using CLI options
        if args.clean:
            pyinstaller_args.append("--clean")
        if args.noconfirm:
            pyinstaller_args.append("--noconfirm")

        # Bundle mode (CLI overrides global default)
        if args.onefile:
            bundle_mode = "onefile"
        elif args.onedir:
            bundle_mode = "onedir"
        else:
            bundle_mode = DEFAULT_BUNDLE_MODE.lower()

        if bundle_mode not in {"onefile", "onedir"}:
            print(f"WARNING: Invalid DEFAULT_BUNDLE_MODE '{DEFAULT_BUNDLE_MODE}', falling back to 'onedir'.")
            bundle_mode = "onedir"

        if bundle_mode == "onefile":
            pyinstaller_args.append("--onefile")

        # Window/console mode
        if args.windowed:
            pyinstaller_args.append("--windowed")

        # Name & icon
        if args.name:
            pyinstaller_args += ["--name", args.name]
        if args.icon:
            icon_path = Path(args.icon)
            if icon_path.exists():
                pyinstaller_args += ["--icon", str(icon_path)]
            else:
                print(f"WARNING: icon not found: {icon_path} (skipping)")

        # Collect Qt and OpenCV resources
        # These flags help avoid missing Qt platform plugin and cv2 DLL issues on Windows.
        # Avoid collecting ALL PySide6 submodules (that can drag in WebEngine, QML, etc.).
        supports_collect_plugins = vparse(PI_VERSION) >= vparse("6.6.0")
        pyinstaller_args += [
            "--collect-data", "PySide6",
        ]
        if supports_collect_plugins:
            pyinstaller_args += ["--collect-plugins", "PySide6"]
        else:
            # Older PyInstaller (<=6.5) doesn't have --collect-plugins; use binaries instead
            pyinstaller_args += ["--collect-binaries", "PySide6"]
        if args.collect_cv2:
            pyinstaller_args += ["--collect-all", "cv2"]

        # Explicitly exclude unused heavy PySide6 modules that cause translation lookups
        # and missing-asset errors (e.g., QtWebEngine locales) when not needed by the app.
        excludes = [
            "PySide6.QtWebEngineCore",
            "PySide6.QtWebEngineWidgets",
            "PySide6.QtWebEngineQuick",
            # Also exclude script helpers that can trigger broad imports in older hooks
            "PySide6.scripts",
            "PySide6.scripts.deploy",
            "PySide6.scripts.project",
        ]
        for mod in excludes:
            pyinstaller_args += ["--exclude-module", mod]

        # Finally, the entry point
        pyinstaller_args.append(str(entry))

    strategy = "--collect-plugins" if (vparse(PI_VERSION) >= vparse("6.6.0")) else "--collect-binaries"
    print(f"Detected PyInstaller {PI_VERSION} (Qt collection via {strategy})")
    try:
        chosen_mode = bundle_mode  # type: ignore[name-defined]
    except NameError:
        chosen_mode = "spec" if args.spec else DEFAULT_BUNDLE_MODE
    print(f"Bundle mode: {chosen_mode}")
    print("Running PyInstaller with arguments:\n  ", " \n  ".join(pyinstaller_args))
    try:
        PyInstaller.__main__.run(pyinstaller_args)  # type: ignore[attr-defined]
    except SystemExit as e:
        # PyInstaller may call sys.exit(), propagate its exit code.
        # Some failures raise SystemExit with a string message; normalize to 1 in that case.
        code = getattr(e, "code", 0)
        try:
            return int(code or 0)
        except Exception:
            print(str(code))
            return 1
    except Exception as e:
        print("PyInstaller failed:", e)
        return 1
    return 0


if __name__ == "__main__":
    ensure_in_project_root()
    sys.exit(main())
