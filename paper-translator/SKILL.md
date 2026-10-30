---
name: paper-translator
description: Translate an English paper PDF into natural, native-sounding Chinese Markdown, with figures, tables, equations, and captions preserved. Use when the user asks to translate a paper/PDF into Chinese, e.g. "把这篇论文翻译成中文", "翻译这个 PDF", "按母语风格翻译论文".
---

# Paper Translator

Turn an English paper PDF into a readable Chinese Markdown document. The output
should read like it was written by a Chinese author, not like a sentence-by-
sentence translation.

## Inputs and outputs

- Input: a PDF path, usually under `papers/`.
- Output document: `translations/<ShortName>-中文翻译.md`.
- Output assets: `translations/assets/<slug>/figN.png`.

If the user does not give a name, derive `<ShortName>` from the paper title or
the first author, and `<slug>` from the short name in lowercase.

## Dependencies

Run this once before translating:

```bash
python3 ~/.qoder/skills/paper-translator/scripts/check_deps.py
```

- **Required**: Python 3.9+ and PyMuPDF. If missing: `pip install pymupdf`.
- **Recommended**: poppler-utils for `pdftotext` / `pdfinfo`.
  If missing: `sudo apt install poppler-utils`.
- **Optional**: Pillow, only for manual image crops.

Do not install system packages without asking the user first. `pip install
pymupdf` is user-level and safe; `sudo apt install poppler-utils` needs
confirmation.

If poppler is unavailable, use `scripts/extract_text.py` instead of
`pdftotext`. The rest of the workflow stays the same.

## Workflow

1. **Read the whole paper first.** Run:
   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/inspect_pdf.py "<paper.pdf>"
   ```
   It prints page count, page-level first lines, figure captions with bounding
   boxes, equation-like lines, and section headings. Then read the full text:

   ```bash
   pdftotext -layout "<paper.pdf>" /tmp/paper.txt
   ```

   If `pdftotext` is missing, use the PyMuPDF fallback:

   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/extract_text.py \
     "<paper.pdf>" --out /tmp/paper.txt
   ```

   Read the text page by page. Make a section/figure/table/equation outline
   before writing anything.

2. **Extract figures.** Run:
   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/extract_figures.py "<paper.pdf>" "translations/assets/<slug>"
   ```
   The script finds `Fig. N:` / `Figure N:` captions with PyMuPDF, takes the
   visual region above each caption, and renders it at 300 DPI. It writes
   `manifest.json` with page numbers and crop boxes.

   Add `--include-text` to pull in nearby short labels and legends (axis
   ticks, percentages, legends) that are text objects, not vector drawings.
   Use `--only 2,7` to process just those figures. The default margin is 8 pt.

   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/extract_figures.py \
     "<paper.pdf>" "translations/assets/<slug>" --include-text --only 6
   ```

   **Always view every PNG with the Read tool.** Check three things: the figure
   is complete, the caption is not included, and no body text is included.
   Re-crop a broken figure with:
   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/extract_figures.py "<paper.pdf>" "translations/assets/<slug>" \
     --override 3:50,60,560,300
   ```
   `--override N:x0,y0,x1,y1` uses PDF points and targets figure N only.
   Repeat until the crop is clean.

3. **Translate.** Follow `reference/style-guide.md`. Use short sentences, active
   voice, and Chinese word order. Translate captions; re-typeset tables as
   Markdown; keep equations in LaTeX with paired `$$`. Do not translate
   references item by item; add a short note with the reference count and arXiv
   link at the end.

4. **Verify.** Run:
   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/check_translation.py "translations/<ShortName>-中文翻译.md"
   ```
   Fix every error. Then audit figure edges:
   ```bash
   python3 ~/.qoder/skills/paper-translator/scripts/audit_figures.py translations
   ```
   Flagged images may be full-bleed photos or table borders, not necessarily
   cut. View each flagged image and re-crop the ones that lost labels, axes, or
   legends. Then read the document once from top to bottom and rewrite any
   sentence that still sounds like translationese.

5. **Update the reading plan** if `reading-plan.md` exists and has a row for this
   paper: add a `· [中文翻译](translations/...)` link.

## Style rules (hard requirements)

- Read the paragraph, then rewrite it in Chinese. Do not follow English word
  order.
- One sentence, one idea. Split long sentences.
- Prefer active voice. Avoid `被……所……`.
- First occurrence of a term: `中文（English）`; after that, Chinese only.
  Keep `session`, `token`, `benchmark` when they are the field's normal usage.
- Keep numbers, units, equation numbers, and citation brackets unchanged.
- Never use these patterns:
  - `使得……`
  - `让……成为可能`
  - `本文提出一种……的方法，它……`
  - `值得注意的是`
  - `具体来说`
  - `另一方面`
  - `通过……来……`
  - `由……组成`
  - chains of three or more `的`

Good example:

> Recent advances in robotics have made it possible to deploy robots in
> real-world settings...
>
> 这几年机器人技术进步很快，把机器人放进真实环境……已经做得到。

Bad example:

> 机器人学的最新进展使得在真实世界部署机器人成为可能。

## Structure

Keep the original reading order: title, authors, abstract, sections, appendix.
Put each figure near the paragraph that first references it. Translate the
caption directly below the image. Use Markdown tables for tables. Use LaTeX for
equations. Add `> 原文：arXiv:...` and `> 项目主页：...` when available.

## Batch mode

When translating several papers, use `reference/subagent-prompt.md` as the
delegation prompt. Give every subagent the same style reference:
`translations/DynaMem-中文翻译.md`. Then run `check_translation.py` yourself on
every output before accepting it.

## Files

- `reference/style-guide.md` — full style rules, substitution table, examples.
- `reference/subagent-prompt.md` — prompt template for parallel translation.
- `scripts/check_deps.py` — dependency check and install hints.
- `scripts/inspect_pdf.py` — outline, captions, equations.
- `scripts/extract_text.py` — PyMuPDF text fallback for `pdftotext`.
- `scripts/extract_figures.py` — caption-based figure cropping (`--include-text`, `--only`, `--override`).
- `scripts/audit_figures.py` — flag images whose content touches the border.
- `scripts/check_translation.py` — banned phrases, image links, math pairs.
- `requirements.txt` — Python dependencies.
