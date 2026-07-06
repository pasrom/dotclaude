#!/usr/bin/env python3
"""Extract the portrait photo from a CV PDF.

Heuristic: portrait photos on CVs are the largest embedded raster image
(by pixel area). We iterate all images on all pages, score them by area,
and pick the winner. Pages 1-2 get a small boost because portraits almost
always sit there.

Usage:
    extract_photo.py <pdf_path> <krz> [--out-dir Profile_Input]

Writes <out-dir>/<KRZ>.jpg and prints the chosen image's dimensions.
Exit code 1 if no embedded image found.
"""
from __future__ import annotations

import argparse
import io
import pathlib
import sys

import fitz  # PyMuPDF
from PIL import Image


def extract(pdf_path: pathlib.Path, krz: str, out_dir: pathlib.Path) -> pathlib.Path | None:
    doc = fitz.open(pdf_path)
    best = None  # (score, page_idx, xref, w, h)
    for page_idx in range(doc.page_count):
        page = doc.load_page(page_idx)
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            pix = fitz.Pixmap(doc, xref)
            w, h = pix.width, pix.height
            area = w * h
            # Skip tiny logos / icons (either dimension < 150px)
            if w < 150 or h < 150:
                pix = None
                continue
            aspect = h / w if w else 0
            # Portraits are roughly upright: 0.8 < h/w < 2.0
            if not (0.8 <= aspect <= 2.0):
                pix = None
                continue
            # Small boost for pages 1-2 where portraits typically sit
            page_boost = 1.3 if page_idx < 2 else 1.0
            score = area * page_boost
            if best is None or score > best[0]:
                best = (score, page_idx, xref, w, h)
            pix = None

    if best is None:
        sys.stderr.write("No embedded photo found (nothing written).\n")
        return None

    _, page_idx, xref, w, h = best
    pix = fitz.Pixmap(doc, xref)
    # PyMuPDF cannot encode a CMYK pixmap as PNG, so convert to RGB *before*
    # tobytes() — CMYK JPEGs are common in print/InDesign CV exports. Pillow's
    # convert("RGB") below then handles any residual alpha.
    if pix.colorspace is not None and pix.colorspace.n >= 4:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{krz}.jpg"
    img.save(out_path, "JPEG", quality=90)

    print(f"OK: {out_path} ({w}x{h}, page {page_idx + 1})")
    return out_path


def main() -> int:
    p = argparse.ArgumentParser(description="Extract portrait photo from CV PDF.")
    p.add_argument("pdf", type=pathlib.Path, help="Path to the CV PDF")
    p.add_argument("krz", help="Candidate abbreviation (3 letters), used as output filename")
    p.add_argument(
        "--out-dir",
        type=pathlib.Path,
        default=pathlib.Path("Profile_Input"),
        help="Output directory (default: Profile_Input/)",
    )
    args = p.parse_args()

    if not args.pdf.exists():
        sys.stderr.write(f"PDF not found: {args.pdf}\n")
        return 1

    result = extract(args.pdf, args.krz, args.out_dir)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
