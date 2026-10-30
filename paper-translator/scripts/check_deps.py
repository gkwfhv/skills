#!/usr/bin/env python3
"""Check the paper-translator skill's dependencies and print install hints."""

import importlib.util
import platform
import shutil
import sys


def status(ok, detail="", install=""):
    return {"ok": ok, "detail": detail, "install": install}


def main():
    rows = []

    py_ok = sys.version_info >= (3, 9)
    rows.append(("Python >= 3.9", status(py_ok, platform.python_version(), "install Python 3.9+")))

    pymupdf_ok = importlib.util.find_spec("pymupdf") is not None
    version = ""
    if pymupdf_ok:
        try:
            import pymupdf
            version = getattr(pymupdf, "__version__", "")
        except Exception:
            pymupdf_ok = False
    rows.append(("PyMuPDF (required)", status(pymupdf_ok, version, "pip install pymupdf")))

    for cmd, pkg in (("pdftotext", "poppler-utils"), ("pdfinfo", "poppler-utils")):
        path = shutil.which(cmd)
        rows.append((f"{cmd} (recommended)", status(bool(path), path or "", f"sudo apt install {pkg}")))

    pillow_ok = importlib.util.find_spec("PIL") is not None
    rows.append(("Pillow (optional)", status(pillow_ok, "", "pip install pillow")))

    width = max(len(r[0]) for r in rows) + 2
    print("Dependency check")
    print("-" * (width + 46))
    for name, s in rows:
        mark = "OK      " if s["ok"] else "MISSING "
        print(f"{name:<{width}} {mark} {s['detail']}")
    print("-" * (width + 46))

    missing_required = [n for n, s in rows if n.startswith("PyMuPDF") and not s["ok"]]
    missing_poppler = [n for n, s in rows if n.startswith(("pdftotext", "pdfinfo")) and not s["ok"]]

    if missing_required:
        print("\nRequired dependency missing:")
        for n, s in rows:
            if n.startswith("PyMuPDF"):
                print(f"  {s['install']}")
        sys.exit(1)

    if missing_poppler:
        print("\npoppler-utils is missing. You can still run the skill:")
        print("  - use scripts/extract_text.py instead of pdftotext")
        print("  - use scripts/inspect_pdf.py / extract_figures.py as usual")
        print("To install: sudo apt install poppler-utils")

    print("\nOK: the skill can run. PyMuPDF alone is enough; poppler is a convenience.")


if __name__ == "__main__":
    main()
