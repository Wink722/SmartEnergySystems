"""Merges the lecture decks into smart_energy_systems.pdf and writes data/slides.json.

The lecture is held by three lecturers and comes as six separate PowerPoint exports.
For the app they are merged into one continuous script; every page gets a chapter,
a part (the official agenda heading), a section, a title, cleaned text and a
graphic flag.

Unlike the sister app, these decks carry **no PDF outline**, so slide titles cannot
be read from the bookmarks. They are recovered from the layout instead: every deck
prints the slide number on its own line, and the title is the run of equally sized
lines that follows it. A font-size heuristic is the fallback.

    python tools/build_slides.py
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "files"
OUT_PDF = ROOT / "smart_energy_systems.pdf"
OUT_JSON = ROOT / "data" / "slides.json"

# Structure of each deck. All page numbers are deck-local and 1-based.
#   content_from  first content page (before that: title and organisational slides)
#   skip          agenda, divider, literature and reference slides: they stay in the
#                 script but drop out of the learning path
#   chapters      (page, number, title) - a deck can span several chapters
#   parts         the official agenda headings of the lecture
#   sections      the finer learning units, each starting at the named page
DECKS = [
    {
        "file": "SmartEnergyInfrastructure WiSe 25-26-Part1.pdf",
        "block": "Gas, Oil and Infrastructure",
        "lecturer": "Dr. Dr. Andrej Pustišek",
        "content_from": 11,
        "skip": [],
        "chapters": [
            (11, 1, "Fundamentals of Energy Infrastructure"),
            (93, 2, "Natural Gas as a Product"),
            (117, 3, "Natural Gas Transport"),
        ],
        "parts": [
            (11, "Terms, Concepts and Fundamentals"),
            (60, "Regulation of Energy Infrastructure"),
            (93, "Natural Gas: Product and Market"),
            (117, "Natural Gas Transport"),
        ],
        "sections": [
            (11, "Energy, units and definitions"),
            (18, "Economies of scale and scope"),
            (24, "Infrastructure: definition and types"),
            (34, "Participants and infrastructure investment"),
            (44, "Transport, storage and networks"),
            (55, "Prices, pricing and fees"),
            (60, "Natural monopoly and unbundling"),
            (72, "Regulation: goals, authorities and forms"),
            (86, "German and European energy law"),
            (93, "Natural gas: value chain and properties"),
            (103, "Gas quality parameters"),
            (112, "Uses and consumption profiles"),
            (117, "Pipeline system and transport capacity"),
            (125, "Pipeline economics: diameter and compression"),
            (133, "Transport principle and European pipelines"),
            (138, "LNG value chain"),
            (150, "LNG trade flows and terminals"),
            (166, "LNG liquefaction and regasification utilisation"),
        ],
    },
    {
        "file": "SmartEnergyInfrastructure WiSe 25-26-Part2.pdf",
        "block": "Gas, Oil and Infrastructure",
        "lecturer": "Dr. Dr. Andrej Pustišek",
        "content_from": 1,
        "skip": [],
        "chapters": [
            (1, 3, "Natural Gas Transport"),
            (33, 4, "Natural Gas Storage"),
            (105, 5, "Oil and Oil Products"),
        ],
        "parts": [
            (1, "Natural Gas Transport"),
            (33, "Natural Gas Storage"),
            (105, "Oil and Oil Product Transport and Storage"),
        ],
        "sections": [
            (1, "Transportation costs"),
            (10, "Transportation contracts"),
            (21, "Transport prices and pricing systems"),
            (33, "Storage basics, parameters and functions"),
            (45, "Storage types and facilities"),
            (53, "Security of supply"),
            (70, "Storage contracts and pricing"),
            (81, "Flexibility and storage components"),
            (89, "Storage regulation"),
            (94, "Gas prices, hubs and swaps"),
            (105, "Crude oil: product, value chain and prices"),
            (120, "Modes of oil transport"),
            (136, "Freight rates and shipping contracts"),
            (144, "Oil storage and stockholding"),
        ],
    },
    {
        "file": "Content Electricity/2025_Smart_Energy_Infrastructures_Part1.pdf",
        "block": "Power Systems Analysis",
        "lecturer": "Dr. Armin Ardone",
        "content_from": 9,
        "skip": [9, 18, 19, 21, 29, 44, 45, 46, 47, 54, 60, 68, 75, 76],
        "chapters": [
            (9, 6, "Introduction to Energy Systems Analysis"),
            (47, 7, "Optimal Unit Commitment"),
        ],
        "parts": [
            (9, "Introduction and overview of energy systems analysis"),
            (47, "Fundamental optimisation models (1): optimal unit commitment"),
        ],
        "sections": [
            (9, "Motivation and goals of energy systems analysis"),
            (21, "Systems representation and modelling"),
            (29, "Model types: bottom-up, top-down, optimisation, simulation"),
            (47, "Linear optimisation: an illustrative example"),
            (54, "Energy markets and the electricity value chain"),
            (60, "Marginal costs and merit order"),
            (68, "Exercise: cost-minimal load coverage"),
        ],
    },
    {
        "file": "Content Electricity/2025_Smart_Energy_Infrastructures_Part2.pdf",
        "block": "Power Systems Analysis",
        "lecturer": "Dr. Armin Ardone",
        "content_from": 4,
        "skip": [9, 10, 11, 14, 19, 25, 36, 48, 52, 53, 54, 56, 60, 70, 72],
        "chapters": [
            (4, 8, "Convolution"),
            (12, 9, "Capacity Expansion Planning"),
            (55, 10, "Scenario Planning"),
        ],
        "parts": [
            (4, "Methods: Convolution"),
            (12, "Fundamental optimisation models (2): optimal capacity expansion"),
            (55, "Methods: Scenario planning approaches"),
        ],
        "sections": [
            (4, "Availability and the convolution method"),
            (12, "Motivation for capacity expansion planning"),
            (14, "Peak-load pricing on a green field"),
            (19, "Expansion planning exercise"),
            (25, "Power plant park and technological development"),
            (36, "Experience curves and learning effects"),
            (48, "Perfect foresight vs. time-step"),
            (55, "Uncertainty and long-term scenarios"),
            (60, "Scenario planning approaches"),
        ],
    },
    {
        "file": "Content Electricity/2025_Smart_Energy_Infrastructures_Part3.pdf",
        "block": "Power Systems Analysis",
        "lecturer": "Dr. Armin Ardone",
        "content_from": 5,
        "skip": [9, 17, 19, 20, 21, 22, 27, 32, 36, 40, 43, 47, 48, 49, 50, 55,
                 72, 74, 75, 76, 84, 93, 99, 102, 106],
        "chapters": [
            (5, 10, "Scenario Planning"),
            (20, 11, "Investment Appraisal"),
            (48, 12, "Decision Making under Uncertainty"),
            (75, 13, "Electricity Grids"),
        ],
        "parts": [
            (5, "Fundamental optimisation models (3): scenarios and power systems analysis"),
            (20, "Methods: Investment appraisal"),
            (48, "Methods: Decision making in the energy sector"),
            (75, "Electricity Grids"),
        ],
        "sections": [
            (5, "Combining scenario planning and energy systems analysis"),
            (10, "Scenario construction for power plant investments"),
            (22, "Compounding and discounting"),
            (27, "Net present value method"),
            (32, "Annuity method"),
            (36, "Internal rate of return"),
            (40, "Discounted payback period"),
            (43, "Comparing investment appraisal methods"),
            (50, "Decision-making environments"),
            (55, "Decision rules under uncertainty"),
            (76, "Electrical fundamentals and transmission losses"),
            (84, "Structure of the power grid and voltage levels"),
            (93, "European grid and market coupling"),
            (99, "System services and control reserve"),
            (102, "Electricity storage options"),
            (106, "Smart grids and the future power supply"),
        ],
    },
    {
        "file": "SEI_H2 and Derivatives_Schuler_Dec2025.pdf",
        "block": "Hydrogen and Derivatives",
        "lecturer": "Julia Schuler",
        "content_from": 2,
        "skip": [12, 13, 14, 66, 84, 97, 103, 116, 127, 140, 150, 158, 159, 160],
        "chapters": [
            (2, 14, "Hydrogen"),
            (67, 15, "Hydrogen Derivatives"),
            (128, 16, "Comparison, Shipping and Metal Fuels"),
        ],
        "parts": [
            (2, "Hydrogen"),
            (67, "Derivatives: ammonia, methanol, LOHC, SNG and PtL"),
            (128, "Comparison, shipping and outlook"),
        ],
        "sections": [
            (2, "Why synthetic energy carriers?"),
            (15, "Hydrogen: status quo and trade"),
            (20, "Electrolysis and hydrogen production"),
            (26, "Hydrogen colours and production potentials"),
            (33, "Hydrogen transport"),
            (41, "Underground hydrogen storage"),
            (44, "Current hydrogen activities and projects"),
            (58, "Challenges, industry example and exercise"),
            (67, "Ammonia"),
            (85, "Methanol and carbon capture"),
            (98, "Liquid organic hydrogen carriers"),
            (104, "Synthetic methane and LNG infrastructure"),
            (117, "Power-to-liquid and Fischer-Tropsch"),
            (128, "Comparison of hydrogen derivatives"),
            (141, "Shipping sector decarbonisation"),
            (151, "Metals as energy carriers"),
        ],
    },
]

# Running heads and footers of the three decks - they repeat on every single page.
FOOTERS = (
    "Smart Energy Infrastructure",
    "Smart Energy Infrastructures",
    "Winter Term 2025/2026",
    "Dr. Dr. Andrej Pustišek",
    "andrej.pustisek@kit.edu",
    "Institute for Industrial Production",
    "Chair of Energy Economics",
    "Dr. Armin Ardone",
    "New Fuels for the Global Energy Transition",
    "J. Schuler",
)

# PowerPoint exports leave Wingdings placeholders behind.
CHAR_MAP = {
    "": "→", "": "→", "": "←", "": "↔",
    "": "• ", "": "• ", "": "- ", "": "• ",
    "": "• ", "": "|", "▪": "• ", "✓": "• ", "\xa0": " ",
}

DATE_RE = re.compile(r"^\d{1,2}\.\d{1,2}\.\d{4}$")
NUM_RE = re.compile(r"^\d{1,4}$")


def clean(text: str) -> str:
    for src, dst in CHAR_MAP.items():
        text = text.replace(src, dst)
    return re.sub(r"[ \t]+", " ", text).strip()


def is_footer(line: str) -> bool:
    if DATE_RE.match(line):
        return True
    return any(f in line for f in FOOTERS)


def lines_of(page: fitz.Page) -> list[tuple[str, float]]:
    """Flat list of (text, font size) in reading order."""
    out: list[tuple[str, float]] = []
    for block in page.get_text("dict")["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            text = clean("".join(s["text"] for s in line["spans"]))
            if not text:
                continue
            size = max((s["size"] for s in line["spans"]), default=0.0)
            out.append((text, round(size, 1)))
    return out


def number_lines(lines: list[tuple[str, float]]) -> list[int]:
    """Indices of stand-alone numeric lines - candidates for the printed number."""
    return [i for i, (t, _) in enumerate(lines) if NUM_RE.match(t)]


def split_title(lines: list[tuple[str, float]], expected: int) -> tuple[int, str, list[str]]:
    """Printed slide number, title and the remaining body lines.

    Every deck prints the slide number on a line of its own and the title follows
    it. Tables and charts contain stand-alone numbers too, so the candidate has to
    match the number this page is expected to carry - otherwise a "2" in a table
    hijacks the title. Falls back to the largest type on the page.
    """
    body = [(t, s) for t, s in lines if not is_footer(t)]

    cands = number_lines(body)
    idx = next((i for i in cands if int(body[i][0]) == expected), None)
    if idx is None:
        idx = next((i for i in cands if abs(int(body[i][0]) - expected) <= 1), None)
    number = int(body[idx][0]) if idx is not None else expected

    title_parts: list[str] = []
    if idx is not None and idx + 1 < len(body):
        size = body[idx + 1][1]
        for text, s in body[idx + 1: idx + 5]:
            if abs(s - size) > 0.6 or len(" ".join(title_parts)) > 110:
                break
            title_parts.append(text)

    rest = [t for i, (t, _) in enumerate(body) if i != idx]
    if title_parts:
        for part in title_parts:
            if part in rest:
                rest.remove(part)
    else:  # fallback: the largest type on the page
        sizes = [s for _, s in body]
        if sizes:
            mx = max(sizes)
            title_parts = [t for t, s in body if s >= mx - 0.6][:3]
            rest = [t for t, s in body if s < mx - 0.6]

    title = " ".join(title_parts).strip()
    if len(title) > 90:
        # No title placeholder on this slide - what we picked up is body text.
        # Shorten it for the heading but leave the wording in the slide text.
        rest = [t for t, _ in body if not NUM_RE.match(t)]
        title = re.split(r"(?<=[.:;?!])\s", title)[0]
        if len(title) > 90:
            title = title[:87].rsplit(" ", 1)[0] + " …"
    return number, title, rest


def lookup(table: list[tuple], page: int):
    """Last entry whose start page is <= page."""
    value = None
    for entry in table:
        if entry[0] <= page:
            value = entry[1:] if len(entry) > 2 else entry[1]
    return value


def main() -> None:
    merged = fitz.open()
    slides: list[dict] = []

    for deck in DECKS:
        src = fitz.open(SRC / deck["file"])
        offset = merged.page_count
        merged.insert_pdf(src)

        # Every deck carries its own furniture on every page - the KIT logo, an
        # institute mark, a divider rule. Counting images against the deck's own
        # floor is the only way to tell a real figure from the letterhead.
        floor_img = sorted(len(p.get_images(full=True)) for p in src)[src.page_count // 2]
        floor_draw = sorted(len(p.get_drawings()) for p in src)[src.page_count // 2]

        # Printed slide numbers rarely equal the PDF page: Part 2 keeps counting
        # where Part 1 stopped, other decks start at zero. Settle the constant
        # offset by majority vote across the whole deck.
        cache = {local: lines_of(src[local - 1]) for local in range(1, src.page_count + 1)}
        deltas = Counter()
        for local, lines in cache.items():
            body = [(t, s) for t, s in lines if not is_footer(t)]
            for i in number_lines(body):
                deltas[int(body[i][0]) - local] += 1
        shift = deltas.most_common(1)[0][0] if deltas else 0

        for local in range(1, src.page_count + 1):
            page = src[local - 1]
            number, title, rest = split_title(cache[local], local + shift)
            content = local >= deck["content_from"] and local not in deck["skip"]
            text = "\n".join(rest)
            chapter = lookup(deck["chapters"], local) if local >= deck["content_from"] else None
            n_images = len(page.get_images(full=True))
            drawings = len(page.get_drawings())

            slides.append({
                "page": offset + local,
                "block": deck["block"],
                "lecturer": deck["lecturer"],
                "chapter": chapter[0] if chapter else 0,
                "chapter_title": chapter[1] if chapter else "Organisation",
                "part": lookup(deck["parts"], local) if content else "",
                "section": lookup(deck["sections"], local) if content else "",
                "title": title or f"Slide {number or local}",
                "text": text,
                "counter": str(number or local),
                "source": Path(deck["file"]).name,
                "source_page": local,
                "graphic": n_images > floor_img
                           or drawings > max(30, 4 * floor_draw)
                           or len(text) < 200,
            })
        src.close()

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(slides, ensure_ascii=False, indent=1), encoding="utf-8")
    merged.set_metadata({"title": "Smart Energy Infrastructure – WS 2025/26",
                         "author": "Pustišek · Ardone · Schuler, KIT"})
    merged.save(OUT_PDF, garbage=3, deflate=True)

    learn = [s for s in slides if s["section"]]
    print(f"{len(slides)} pages -> {OUT_PDF.name} ({OUT_PDF.stat().st_size/1e6:.1f} MB)")
    print(f"{len(learn)} content slides in "
          f"{len({(s['chapter'], s['section']) for s in learn})} sections")
    for ch in sorted({s["chapter"] for s in learn}):
        pages = [s for s in learn if s["chapter"] == ch]
        print(f"  Chapter {ch:>2}: {len(pages):>3} slides, "
              f"{len({s['section'] for s in pages})} sections, "
              f"{sum(1 for s in pages if s['graphic'])} graphic-heavy  "
              f"[{pages[0]['chapter_title']}]")


if __name__ == "__main__":
    main()
