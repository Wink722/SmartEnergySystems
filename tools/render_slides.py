"""Renders every content slide of the merged script to PNG.

Authoring aid, not needed at runtime: the question authors have to see the figure
on a slide rather than guess from its title. Output lands in .slides_png/ (ignored
by git) and is named by the global page number used everywhere else in the app.

    python tools/render_slides.py [--all] [--dpi 110]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "smart_energy_systems.pdf"
SLIDES = ROOT / "data" / "slides.json"
OUT = ROOT / ".slides_png"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="including organisational slides")
    ap.add_argument("--dpi", type=int, default=110)
    args = ap.parse_args()

    slides = json.loads(SLIDES.read_text(encoding="utf-8"))
    wanted = [s for s in slides if args.all or s["section"]]
    OUT.mkdir(exist_ok=True)

    doc = fitz.open(PDF)
    zoom = args.dpi / 72
    for s in wanted:
        pix = doc[s["page"] - 1].get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        pix.save(OUT / f"{s['page']:04d}.png")
    doc.close()

    size = sum(f.stat().st_size for f in OUT.glob("*.png")) / 1e6
    print(f"{len(wanted)} slides -> {OUT.relative_to(ROOT)}/ ({size:.0f} MB at {args.dpi} dpi)")


if __name__ == "__main__":
    main()
