#!/usr/bin/env python3
"""Print a paper's structure: pages, captions, equations, headings."""

import argparse
import re
import sys

try:
    import pymupdf
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")

CAP_RE = re.compile(r"^(?:Fig\.|Figure)\s*(\d+)\s*[:.]", re.I)
SEC_RE = re.compile(r"^(?:[IVXLC]+\.|\d+\.|[A-Z]\.)\s+\S")
EQ_RE = re.compile(r"\(\d+\)\s*$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="page range, e.g. 1-8")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    print(f"file: {args.pdf}")
    print(f"pages: {doc.page_count}")
    print(f"metadata title: {doc.metadata.get('title', '')}")

    start, end = 1, doc.page_count
    if args.pages:
        a, _, b = args.pages.partition("-")
        start = int(a)
        end = int(b or a)

    for pno in range(start - 1, min(end, doc.page_count)):
        page = doc[pno]
        blocks = [b for b in page.get_text("blocks") if b[4].strip()]
        print(f"\n=== PAGE {pno + 1} ===")
        heads = [b for b in blocks if SEC_RE.match(b[4].strip())]
        for b in heads[:6]:
            print(f"  heading: {b[4].strip()[:80]}")
        caps = [b for b in blocks if CAP_RE.match(b[4].strip())]
        for b in caps:
            num = CAP_RE.match(b[4].strip()).group(1)
            box = ",".join(f"{v:.1f}" for v in b[:4])
            print(f"  figure {num}: bbox=({box})  {b[4].strip()[:60]}")
        eqs = [b for b in blocks if EQ_RE.search(b[4].strip())]
        for b in eqs[:8]:
            print(f"  equation: {b[4].strip()[:80]}")
        first = [b[4].strip().replace("\n", " ") for b in blocks[:3]]
        for line in first:
            print(f"  first: {line[:90]}")

    print("\nNext: pdftotext -layout <pdf> /tmp/paper.txt, then read it page by page.")


if __name__ == "__main__":
    main()
