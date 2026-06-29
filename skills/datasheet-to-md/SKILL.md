---
name: datasheet-to-md
description: Convert a PDF datasheet (or any technical PDF) into clean, LLM-friendly Markdown with extracted images, then review the result for fidelity. Trigger when the user wants to convert/ingest a datasheet PDF to Markdown, add a datasheet to a datasheet library/repo, or make a PDF searchable for an LLM. Handles the non-obvious pymupdf failure modes (Symbol-font glyphs extracted as invisible Private-Use code points, vector figures that don't extract, collapsed tables).
argument-hint: path to a PDF (and optionally a component name / target repo)
---

# Skill: datasheet-to-md

Convert a PDF datasheet to clean Markdown, then **review it** — conversion is never the end; a datasheet is only useful if its tables and numbers survived.

## 0. Get the file (macOS gotcha)

If the PDF is in `~/Downloads` and reads fail with `Operation not permitted` / `EPERM` (TCC blocks the terminal/host app — `stat` works but `cp`/`mv`/Read do not), do **not** fight it: create the target dir, `open` it in Finder, and ask the user to drag the PDF in (Finder holds the grant; the `!`-prefix trick runs in the same blocked process and won't help).

## 1. Convert

```bash
python3 <skill-dir>/convert_datasheet.py <pdf_path> [--name NAME] [--out-dir DIR]
```

- Requires `pymupdf4llm` (`pip install pymupdf4llm`).
- `--name` = output base name (default: sanitized PDF stem). `--out-dir` defaults to the PDF's directory.
- Writes `<out-dir>/<NAME>.md` and `<out-dir>/<NAME>_media/*.png` (PNG @ 200 DPI, **relative** image paths).
- Flags: `--dpi N`, `--no-glyph-fix`, `--render-pages 41,77` (see below).

The script handles two non-obvious pymupdf failure modes, plus verification:
1. **Symbol-font glyphs as invisible code points.** pymupdf extracts Adobe Symbol glyphs as Private-Use chars (`U+F0xx`), so `Ω`, `µ`, `°`, `≥`, `×`, `θ`, `Δ`/`Σ`, `©` look *missing* — e.g. a `kΩ` cell renders as bare `k`, `120 mΩ` as `120 m`. It remaps them to real Unicode and strips Symbol leader-dots (guarded so real decimal points are never deleted).
2. **Verification.** Reports broken image refs (must be 0) and residual `PUA`/`U+FFFD` (acceptable only inside equation bracket-segments and fenced figure picture-text).

Read the script's printed report. **0 broken refs is required.**

**Vector figures (explicit, not automatic).** Schematics/plots drawn as vectors sometimes produce no image (caption-only). Auto-detecting which ones pymupdf4llm missed is unreliable (it rasterizes *some* vector graphics but not others), so it is **explicit**: during review (step 2) note the PDF pages that have a figure caption but no image, then re-run with `--render-pages 41,77` — those pages are rendered (header/footer cropped) and inserted right before their Markdown caption. Re-running is safe (idempotent); pass `--render-pages` together with the same `--name`/`--out-dir`.

## 2. Review the Markdown (do not skip)

The converter cannot judge meaning. Open the `.md` and compare against the PDF. For long datasheets, fan out one review subagent per file. Check, with PASS/PARTIAL/FAIL + evidence (cite md line + PDF page):

- **Identity** — confirm the exact part number(s), manufacturer, document revision from the content (download filenames are often wrong/misleading — verify and rename if so).
- **Structure** — all sections present, no dropped page spans.
- **Tables** (most important) — Electrical Characteristics, Pin/Function, Abs-Max, Register maps. Are rows/columns intact, or **collapsed into prose**? A table that became a run-on paragraph (common on OCR'd pages) must be **transcribed back into a real Markdown table from the PDF** — by hand, verifying every value. Do not trust the jumbled OCR order.
- **OCR pages** — the converter prints which pages used OCR; check those regions for garbled numbers (O↔0, l↔1, lost decimals).
- **Numbers/units** — spot-check key specs against the PDF. After the glyph fix, confirm units like `kΩ`/`mΩ`/`µA`/`°C` are present.
- **Residual artifacts** — strikethrough noise (`~~...~~`), repeated header/footer/copyright lines, `�`. Strip strikethrough/leader noise from tables; header/footer pollution is low priority.

Fix what's spec-relevant; document (don't silently leave) what you couldn't recover.

## 3. (Optional) Add to a datasheet library repo

If adding to `datasheet-library` (or any repo with that convention):

- One directory per component: `<component>/<component>.pdf`, `<component>.md`, `<component>_media/`.
- Rename the source PDF to the clean component name.
- PDFs and images go to **Git LFS** (`.gitattributes`: `*.pdf`, `*.png` → lfs). Run `git lfs install` once.
- Add a row to the repo `README.md` component table.
- Commit (`feat(<component>): add ... datasheet`); a second `fix(<component>): post-conversion QA pass` commit if you transcribed tables / rendered figures keeps an honest audit trail.
- If the repo is a submodule, push it first, then bump the parent pointer. **Pushing publishes** — confirm before pushing a parent that carries unrelated unpushed commits.

## Notes

- Conversion settings (200 DPI, relative paths) match the `datasheet-library` convention so output drops straight in.
- The glyph map is the validated Adobe-Symbol subset; equation bracket-segments (`U+F0E6/F6/E8/F8`) are intentionally left (multi-line glyphs not safely mappable).
