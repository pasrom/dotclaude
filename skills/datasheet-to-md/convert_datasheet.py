#!/usr/bin/env python3
"""Convert a PDF datasheet into clean, LLM-friendly Markdown.

Pipeline (all generic, no per-part hardcoding):
  1. pymupdf4llm -> Markdown with extracted images (PNG, relative paths).
  2. Repair Adobe Symbol-font glyphs that pymupdf extracts as Private-Use-Area
     code points (the classic "the Omega/mu/degree symbol is invisibly there as
     U+F0xx" bug): remap to real Unicode; strip Symbol leader-dots (guarded so a
     real decimal point is never deleted).
  3. (--render-pages) Render specific PDF pages whose vector figures pymupdf4llm
     failed to extract, and insert them at the figure caption.
  4. Verify: every image reference resolves; report residual PUA / U+FFFD.

Requires: pymupdf4llm, pymupdf  (pip install pymupdf4llm)

Usage:
  python3 convert_datasheet.py PDF [--name NAME] [--out-dir DIR] [--dpi 200]
                                   [--no-glyph-fix] [--render-pages 41,77]

Defaults: NAME = sanitized PDF stem; out-dir = the PDF's directory.
Writes <out-dir>/<NAME>.md and <out-dir>/<NAME>_media/*.png

Auto-detecting which figures pymupdf4llm missed is unreliable (it rasterizes
*some* vector graphics but not others). So figure rendering is explicit: during
review, note pages with a caption but no image, then re-run with --render-pages.
"""
import argparse
import collections
import os
import re
import sys

# Adobe Symbol encoding: pymupdf emits Symbol-font glyphs as U+F0NN (= byte 0xNN).
# Only confident, unambiguous mappings are listed.
SYMBOL_MAP = {
    0xF057: "Ω", 0xF06D: "µ", 0xF070: "π", 0xF071: "θ", 0xF044: "Δ",
    0xF053: "Σ", 0xF0B0: "°", 0xF0B1: "±", 0xF0B3: "≥", 0xF0A3: "≤",
    0xF0B4: "×", 0xF0B7: "·", 0xF0E3: "©", 0xF0E2: "®", 0xF028: "(",
    0xF029: ")", 0xF05B: "[", 0xF05D: "]", 0xF03E: ">", 0xF03C: "<",
    0xF020: " ", 0xF0A4: "/", 0xF03B: ";",
}
LEADER = 0xF02E  # Symbol '.' used as decorative leader dots
CYRILLIC_FIX = {"Ө": "θ", "ө": "θ"}  # OCR look-alikes for Greek theta

CAPTION_RE = re.compile(r"(?:FIGURE|Figure|Fig\.?)\s*\d", re.IGNORECASE)


def sanitize(stem: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", stem.strip().lower()).strip("-")
    return s or "datasheet"


def fix_glyphs(md: str):
    counts = collections.Counter()
    for cp, v in SYMBOL_MAP.items():
        n = md.count(chr(cp))
        if n:
            md = md.replace(chr(cp), v)
            counts[f"U+{cp:04X}->{v}"] = n
    for bad, good in CYRILLIC_FIX.items():
        n = md.count(bad)
        if n:
            md = md.replace(bad, good)
            counts[f"{bad}->{good}"] = n
    lead = chr(LEADER)
    if lead in md:
        risky = any(md[i - 1:i].isdigit() and md[i + 1:i + 2].isdigit()
                    for i, c in enumerate(md) if c == lead)
        if not risky:
            counts["leader-dots->del"] = md.count(lead)
            md = md.replace(lead, "")
    return md, counts


def page_text(page) -> str:
    t = page.get_text()
    return t if isinstance(t, str) else ""


def caption_label(text: str):
    """Figure label of the first real caption on the page (one with a colon,
    e.g. 'FIGURE 7-1:' -> '7-1'); references like 'see Figure 7-1' are ignored."""
    m = re.search(r"(?:FIGURE|Figure)\s+([0-9]+-[0-9]+|[0-9]+)\s*[:.]", text)
    return m.group(1) if m else None


def insert_before_md_caption(md: str, label: str, ref: str):
    """Insert ref before the Markdown caption line for this figure label."""
    pat = re.compile(r"^.{0,8}\*\*\s*(?:FIGURE|Figure)\s+" + re.escape(label) + r"\b",
                     re.IGNORECASE | re.MULTILINE)
    m = pat.search(md)
    if not m:
        return md, False
    line_start = md.rfind("\n", 0, m.start()) + 1
    return md[:line_start] + ref + "\n\n" + md[line_start:], True


def render_pages(pdf_path, pages, media_dir, media_rel, name, md, dpi):
    """Render the given 1-based PDF pages (cropped header/footer) and insert
    each before its Markdown figure caption; append to a Rendered Figures
    section if the caption can't be located."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    done, appended = [], []
    for pno in pages:
        if pno < 1 or pno > doc.page_count:
            print(f"  --render-pages: page {pno} out of range (1..{doc.page_count})")
            continue
        page = doc[pno - 1]
        r = page.rect
        clip = pymupdf.Rect(r.x0, r.y0 + r.height * 0.04, r.x1, r.y1 - r.height * 0.06)
        fn = f"{name}.pdf-{pno:04d}-fullpage.png"
        page.get_pixmap(dpi=dpi, clip=clip).save(os.path.join(media_dir, fn))
        ref = f"![]({media_rel}/{fn})"
        if ref in md:
            done.append(pno)
            continue
        label = caption_label(page_text(page))
        placed = False
        if label:
            md, placed = insert_before_md_caption(md, label, ref)
        if not placed:
            md += f"\n\n{ref}\n_Rendered from PDF page {pno}._\n"
            appended.append(pno)
        done.append(pno)
    if appended:
        print(f"  (caption not found for page(s) {appended} -> appended at end)")
    return md, done


def verify(md: str, out_dir: str):
    refs = re.findall(r"\]\(([^)]+\.png)\)", md)
    broken = [r for r in refs if not os.path.isfile(os.path.join(out_dir, r))]
    pua = sum(1 for c in md if 0xE000 <= ord(c) <= 0xF8FF)
    fffd = md.count("�")
    return refs, broken, pua, fffd


def main():
    ap = argparse.ArgumentParser(description="PDF datasheet -> clean Markdown")
    ap.add_argument("pdf")
    ap.add_argument("--name", help="output base name (default: sanitized PDF stem)")
    ap.add_argument("--out-dir", help="output dir (default: the PDF's directory)")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--no-glyph-fix", action="store_true", help="skip Symbol-font glyph repair")
    ap.add_argument("--render-pages", help="comma-separated 1-based PDF pages to render as figures, e.g. 41,77")
    args = ap.parse_args()

    try:
        import pymupdf4llm
    except ImportError:
        sys.exit("ERROR: pymupdf4llm not installed.  pip install pymupdf4llm")

    pdf = os.path.abspath(args.pdf)
    if not os.path.isfile(pdf):
        sys.exit(f"ERROR: not found: {pdf}")
    name = args.name or sanitize(os.path.splitext(os.path.basename(pdf))[0])
    out_dir = os.path.abspath(args.out_dir) if args.out_dir else os.path.dirname(pdf)
    media_rel = f"{name}_media"
    media_dir = os.path.join(out_dir, media_rel)
    os.makedirs(media_dir, exist_ok=True)

    cwd = os.getcwd()
    os.chdir(out_dir)  # run from out_dir so image_path (and refs) stay relative
    try:
        print(f"converting {os.path.basename(pdf)} -> {name}.md ...", flush=True)
        md = pymupdf4llm.to_markdown(pdf, write_images=True, image_path=media_rel,
                                     image_format="png", dpi=args.dpi)
        if not isinstance(md, str):
            md = "\n\n".join(str(x) for x in md)
    finally:
        os.chdir(cwd)

    if not args.no_glyph_fix:
        md, gcounts = fix_glyphs(md)
        if gcounts:
            print("  glyph fixes:", dict(gcounts))

    if args.render_pages:
        try:
            pages = [int(x) for x in args.render_pages.replace(" ", "").split(",") if x]
        except ValueError:
            sys.exit("ERROR: --render-pages must be a comma list of integers, e.g. 41,77")
        md, done = render_pages(pdf, pages, media_dir, media_rel, name, md, args.dpi)
        print(f"  rendered figure page(s): {done}")

    md_path = os.path.join(out_dir, f"{name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    refs, broken, pua, fffd = verify(md, out_dir)
    n_imgs = len([f for f in os.listdir(media_dir) if f.endswith(".png")])
    print(f"\nWROTE {md_path}")
    print(f"  {len(md)} chars, {n_imgs} images, {len(refs)} image refs, {len(broken)} broken")
    for b in broken:
        print(f"    BROKEN REF: {b}")
    print(f"  residual PUA glyphs: {pua}  (equation bracket-segments / unmapped)")
    print(f"  residual U+FFFD (lost OCR glyphs): {fffd}")
    print("\nNEXT: review the .md against the PDF (identity, tables, numbers/units,")
    print("      OCR'd pages). Transcribe any table that collapsed to prose from the")
    print("      PDF. For figures with a caption but no image, re-run --render-pages.")


if __name__ == "__main__":
    main()
