#!/usr/bin/env python3
"""Flag translated figures whose content touches the image border."""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


def edge_fraction(img, side, border):
    w, h = img.size
    box = {
        "top": (0, 0, w, border),
        "bottom": (0, h - border, w, h),
        "left": (0, 0, border, h),
        "right": (w - border, 0, w, h),
    }[side]
    strip = img.crop(box).convert("RGB")
    pixels = list(strip.getdata())
    if not pixels:
        return 0.0
    nonwhite = sum(1 for r, g, b in pixels if min(r, g, b) < 245)
    return nonwhite / len(pixels)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", help="Markdown files or directories")
    ap.add_argument("--threshold", type=float, default=0.02,
                    help="non-white fraction on an edge that counts as tight")
    ap.add_argument("--border", type=int, default=2, help="border width in pixels")
    ap.add_argument("--json", help="write results to this JSON file")
    args = ap.parse_args()

    mds = []
    for p in args.paths:
        p = Path(p)
        if p.is_dir():
            mds.extend(sorted(p.glob("*.md")))
        elif p.suffix == ".md":
            mds.append(p)

    seen = set()
    rows = []
    for md in mds:
        text = md.read_text(encoding="utf-8")
        for link in IMG_RE.findall(text):
            if link.startswith("http"):
                continue
            path = (md.parent / link).resolve()
            if path in seen or not path.exists():
                continue
            seen.add(path)
            try:
                img = Image.open(path)
            except Exception as e:
                rows.append({"image": str(path), "error": str(e)})
                continue
            fr = {s: edge_fraction(img, s, args.border) for s in ("top", "bottom", "left", "right")}
            tight = [s for s, v in fr.items() if v > args.threshold]
            rows.append({
                "image": str(path),
                "size": list(img.size),
                "edges": {s: round(v, 4) for s, v in fr.items()},
                "tight": tight,
            })

    rows.sort(key=lambda r: (-len(r.get("tight", [])), r["image"]))
    print(f"{'image':<58}{'size':>12}  {'top':>6}{'bottom':>7}{'left':>6}{'right':>6}  tight")
    print("-" * 120)
    flagged = 0
    for r in rows:
        if "error" in r:
            print(f"{r['image']:<58} ERROR {r['error']}")
            continue
        e = r["edges"]
        mark = ",".join(r["tight"]) if r["tight"] else ""
        if r["tight"]:
            flagged += 1
        print(f"{Path(r['image']).name:<58}{str(tuple(r['size'])):>12}  "
              f"{e['top']:>6.3f}{e['bottom']:>7.3f}{e['left']:>6.3f}{e['right']:>6.3f}  {mark}")

    print(f"\n{len(rows)} images, {flagged} flagged (threshold={args.threshold}, border={args.border}px)")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
