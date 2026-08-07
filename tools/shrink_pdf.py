"""Rewrites a PDF with compression and garbage collection.

fitz.DocumentWriter, which sets the booklets, writes uncompressed content
streams, and the figure appendix is appended incrementally on top - an
incremental save only ever adds bytes, it never tidies up. The result was a
61 MB file for 49 pages of text and 18 images. A full rewrite with deflate and
garbage collection brings the same content down to under 4 MB.

    python tools/shrink_pdf.py "file.pdf"                # writes "file (small).pdf"
    python tools/shrink_pdf.py "file.pdf" --in-place     # replaces it
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

import fitz


def shrink(path: str, in_place: bool = False) -> str:
    src_size = os.path.getsize(path)
    stem, ext = os.path.splitext(path)
    out = path if in_place else f"{stem} (small){ext}"

    doc = fitz.open(path)
    pages, text = doc.page_count, doc[0].get_text()
    tmp = tempfile.mktemp(suffix=".pdf")
    doc.save(tmp, garbage=4, deflate=True, deflate_images=True,
             deflate_fonts=True, clean=True)
    doc.close()

    # Never hand back something that lost content.
    check = fitz.open(tmp)
    ok = check.page_count == pages and check[0].get_text() == text
    check.close()
    if not ok:
        os.remove(tmp)
        raise SystemExit(f"{os.path.basename(path)}: content changed, not written")

    shutil.move(tmp, out)
    print(f"{os.path.basename(path)}: {src_size/1e6:.1f} MB -> "
          f"{os.path.getsize(out)/1e6:.1f} MB  ({os.path.basename(out)})")
    return out


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        raise SystemExit(2)
    in_place = "--in-place" in sys.argv
    for path in args:
        shrink(path, in_place)


if __name__ == "__main__":
    main()
