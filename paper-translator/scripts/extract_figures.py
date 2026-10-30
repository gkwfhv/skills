#!/usr/bin/env python3
"""Crop figures from a paper by locating Fig./Figure captions with PyMuPDF."""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")

CAP_RE = re.compile(r"^(?:Fig\.|Figure)\s*(\d+)\s*[:.]", re.I)


def union(rects):
    r = pymupdf.Rect(rects[0])
    for x in rects[1:]:
        r |= x
    return r


def parse_overrides(values):
    out = {}
    for v in values or []:
        try:
            num, rest = v.split(":", 1)
            x0, y0, x1, y1 = (float(t) for t in rest.split(","))
            out[int(num)] = pymupdf.Rect(x0, y0, x1, y1)
        except ValueError:
            sys.exit(f"bad --override: {v}; expected N:x0,y0,x1,y1")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("--margin", type=float, default=8.0, help="extra margin in PDF points")
    ap.add_argument("--include-text", action="store_true",
                    help="include short labels/legends above the caption in the crop")
    ap.add_argument("--only", help="comma-separated figure numbers to process")
    ap.add_argument("--override", action="append", metavar="N:x0,y0,x1,y1")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    overrides = parse_overrides(args.override)
    only = {int(x) for x in args.only.split(",")} if args.only else None

    doc = pymupdf.open(args.pdf)
    manifest = []

    for pno in range(doc.page_count):
        page = doc[pno]
        blocks = [b for b in page.get_text("blocks") if b[4].strip()]
        captions = []
        for b in blocks:
            m = CAP_RE.match(b[4].strip())
            if m:
                captions.append((int(m.group(1)), b))
        if not captions:
            continue

        page_w, page_h = page.rect.width, page.rect.height
        dict_blocks = page.get_text("dict")["blocks"]
        visuals = []
        for b in dict_blocks:
            if b.get("type") != 1:
                continue
            r = pymupdf.Rect(b["bbox"])
            # Skip full-page backgrounds and page-edge artefacts.
            if r.width > page_w * 0.95 or r.height > page_h * 0.7:
                continue
            if r.y0 < 30 or r.y1 > page_h - 20:
                continue
            visuals.append(r)
        for d in page.get_drawings():
            r = pymupdf.Rect(d["rect"])
            if r.width > page_w * 0.95 or r.height > page_h * 0.5:
                continue
            if r.y0 < 30 or r.y1 > page_h - 20:
                continue
            if r.width > 3 or r.height > 3:
                visuals.append(r)

        captions.sort(key=lambda item: item[1][1])
        for idx, (num, cap) in enumerate(captions):
            if only is not None and num not in only:
                continue
            if overrides and num not in overrides:
                continue
            cap_r = pymupdf.Rect(cap[:4])
            # Do not let a figure swallow an earlier figure in the same column.
            lower = 30
            for _, prev_cap in captions[:idx]:
                prev_r = pymupdf.Rect(prev_cap[:4])
                if not (prev_r.x1 <= cap_r.x0 or cap_r.x1 <= prev_r.x0):
                    lower = max(lower, prev_r.y1 + 4)
            if num in overrides:
                box = pymupdf.Rect(overrides[num])
            else:
                cand = []
                for r in visuals:
                    if r.y1 > cap_r.y0 + 1 or r.y0 < max(lower, cap_r.y0 - 750):
                        continue
                    # The visual must sit inside this caption's column.
                    if r.x1 < cap_r.x0 - 20 or r.x0 > cap_r.x1 + 20:
                        continue
                    cx = (r.x0 + r.x1) / 2
                    if cx < cap_r.x0 - 20 or cx > cap_r.x1 + 20:
                        continue
                    cand.append(r)
                if cand:
                    box = union(cand)
                else:
                    prev = [
                        b for b in blocks
                        if b[3] < cap_r.y0 - 1 and not CAP_RE.match(b[4].strip())
                    ]
                    if prev:
                        p = max(prev, key=lambda b: b[3])
                        box = pymupdf.Rect(cap_r.x0, p[3] + 4, cap_r.x1, cap_r.y0 - 2)
                    else:
                        box = pymupdf.Rect(cap_r.x0, 36, cap_r.x1, cap_r.y0 - 2)

            if args.include_text and num not in overrides:
                text_rects = []
                for b in blocks:
                    text = " ".join(b[4].split())
                    if not text or CAP_RE.match(text):
                        continue
                    r = pymupdf.Rect(b[:4])
                    if r.y1 > cap_r.y0 - 1 or r.y0 < lower:
                        continue
                    # Only short labels/legends, not body paragraphs.
                    if len(text) > 90 or r.height > 30 or r.width > page_w * 0.75:
                        continue
                    words = len(text.split())
                    if r.y1 <= box.y0:
                        # Labels above the figure: must be very close and short.
                        if box.y0 - r.y1 > 10 or words > 4:
                            continue
                    elif r.y0 >= box.y1:
                        # Legends below the figure: allow longer, but stay close.
                        if r.y0 - box.y1 > 30 or words > 25:
                            continue
                    else:
                        # Text vertically inside the figure: only short labels.
                        if words > 6:
                            continue
                    # Text must sit inside the figure's horizontal span.
                    if r.x0 < box.x0 - 10 or r.x1 > box.x1 + 10:
                        continue
                    if r.width > box.width * 0.95:
                        continue
                    text_rects.append(r)
                if text_rects:
                    box = union([box] + text_rects)

            m = args.margin
            box = pymupdf.Rect(
                max(0, box.x0 - m),
                max(0, box.y0 - m),
                min(page.rect.x1, box.x1 + m),
                min(page.rect.y1, box.y1 + m),
            )
            box.y1 = min(box.y1, cap_r.y0 - 2)
            if lower > 30:
                box.y0 = max(box.y0, lower)
            if box.width < 20 or box.height < 20:
                print(f"WARN page {pno + 1} figure {num}: crop too small, skipped")
                continue

            path = outdir / f"fig{num}.png"
            pix = page.get_pixmap(clip=box, dpi=args.dpi)
            pix.save(path)
            item = {
                "figure": num,
                "page": pno + 1,
                "bbox_pdf_points": [round(v, 1) for v in box],
                "path": str(path),
                "width": pix.width,
                "height": pix.height,
            }
            manifest.append(item)
            print(f"OK page {pno + 1} figure {num}: {box} -> {path} ({pix.width}x{pix.height})")

    (outdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n{len(manifest)} figures -> {outdir}")
    print("Now open every PNG, check for cut-off figures or included captions/body text.")


if __name__ == "__main__":
    main()
