#!/usr/bin/env python3
"""Check a translated Markdown file for style and structural problems."""

import argparse
import re
import sys
from pathlib import Path

BANNED = [
    ("使得", re.compile(r"使得")),
    ("让…成为可能", re.compile(r"让[^。！？\n]{0,30}成为可能")),
    ("本文提出", re.compile(r"本文提出")),
    ("值得注意的是", re.compile(r"值得注意的是")),
    ("具体来说", re.compile(r"具体来说")),
    ("另一方面", re.compile(r"另一方面")),
    ("通过…来…", re.compile(r"通过[^。！？\n]{0,20}来")),
    ("由…组成", re.compile(r"由[^。！？\n]{0,20}组成")),
]

# Broad patterns that are often false positives; report but do not fail.
SOFT = [
    ("被…所…", re.compile(r"被[^。！？\n]{0,12}所")),
]

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
PARA_SPLIT = re.compile(r"\n\s*\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    args = ap.parse_args()

    path = Path(args.md)
    text = path.read_text(encoding="utf-8")
    errors = []
    warnings = []

    images = IMG_RE.findall(text)
    for img in images:
        if re.match(r"^https?://", img):
            continue
        target = (path.parent / img).resolve()
        if not target.exists():
            errors.append(f"missing image: {img}")

    if text.count("$$") % 2:
        errors.append(f"unpaired $$: {text.count('$$')} occurrences")

    for name, rx in BANNED:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            errors.append(f"banned phrase '{name}' at line {line}")

    for name, rx in SOFT:
        for m in rx.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            warnings.append(f"check phrase '{name}' at line {line} (may be a false positive)")

    for heading in ("摘要", "参考文献"):
        if heading not in text:
            warnings.append(f"missing heading: {heading}")

    paragraphs = [p.strip() for p in PARA_SPLIT.split(text) if p.strip()]
    for p in paragraphs:
        if p.startswith(("#", "![", "|", "$$", ">")):
            continue
        cn = len(re.findall(r"[\u4e00-\u9fff]", p))
        en = len(re.findall(r"[A-Za-z]", p))
        if cn and en > cn * 1.5:
            warnings.append(f"mostly-English paragraph: {p[:70]!r}")

    print(f"file: {path}")
    print(f"images: {len(images)}  tables: {sum(1 for l in text.splitlines() if l.startswith('|---'))}  "
          f"display math: {text.count('$$') // 2}  chars: {len(text)}")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    print(f"\nOK: no errors, {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
