#!/usr/bin/env python3
"""Extract text from a PDF with PyMuPDF. Fallback when pdftotext is unavailable."""

import argparse
import sys

try:
    import pymupdf
except ImportError:
    sys.exit("PyMuPDF is required: pip install pymupdf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="page range, e.g. 1-8")
    ap.add_argument("--out", help="write to this file instead of stdout")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    start, end = 1, doc.page_count
    if args.pages:
        a, _, b = args.pages.partition("-")
        start = int(a)
        end = int(b or a)

    chunks = []
    for pno in range(start - 1, min(end, doc.page_count)):
        page = doc[pno]
        chunks.append(f"\n===== PAGE {pno + 1} =====\n")
        chunks.append(page.get_text("text", sort=True))
    text = "".join(chunks)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {args.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()
