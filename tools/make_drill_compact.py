"""Builds the compact, black-and-white exam drill.

Differences to tools/make_drill.py, which produced the first edition:
  * answers are the short exam-style ones from tools/answers_compact.json
  * pure black on white - no colour, no shading, no rules. A mono laser printer
    reproduces it exactly as designed; question and answer are told apart by
    weight and spacing alone.
  * formulas sit on their own indented line with real subscripts
  * comparison answers are set as borderless tables

    python tools/select_compact.py        # choose the questions
    python tools/make_drill_compact.py    # set the booklet
"""

from __future__ import annotations

import html as H
import json
import os
import re

import fitz

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEL = os.path.join(ROOT, "tools", "selection_compact.json")
ANS = os.path.join(ROOT, "tools", "answers_compact.json")
PNG = os.path.join(ROOT, ".slides_png")
OUT = os.path.join(os.path.dirname(ROOT),
                   "Exam Drill compact - print version.pdf")

CSS = """
* { font-family: sans-serif; color: #000000; }
body { font-size: 8.8pt; line-height: 1.34; }
h1 { font-size: 27pt; margin-bottom: 3pt; line-height: 1.05; }
h2 { font-size: 13pt; margin-top: 17pt; margin-bottom: 5pt; }
p  { margin-top: 0pt; margin-bottom: 4pt; }
.lead { font-size: 11pt; margin-bottom: 9pt; }
.eyebrow { font-size: 8pt; letter-spacing: 1pt; margin-bottom: 11pt; }
.meta { font-size: 7.6pt; margin-bottom: 1pt; }
.q { font-size: 9.2pt; margin-bottom: 3pt; }
.a { margin-bottom: 13pt; }
.bul { margin-left: 9pt; text-indent: -9pt; margin-bottom: 1pt; }
.frm { margin-left: 14pt; margin-top: 3pt; margin-bottom: 3pt; font-size: 9pt; }
.opt { margin-left: 9pt; margin-bottom: 1pt; }
.note { font-size: 8.2pt; margin-top: 2pt; }
.fig { font-size: 8pt; margin-bottom: 3pt; }
.small { font-size: 8pt; }
.key { font-size: 8.6pt; margin-bottom: 3pt; }
table { font-size: 8.2pt; margin-top: 3pt; margin-bottom: 4pt; }
th { text-align: left; padding: 1pt 8pt 2pt 0pt; }
td { padding: 1pt 8pt 1pt 0pt; vertical-align: top; }
"""

# X_abc -> X with a real subscript. Applied after HTML escaping, so the
# underscore is still there and the letters are safe.
SUB = re.compile(r"([A-Za-zͰ-Ͽ\)])_([A-Za-z0-9]+)")


def dots(n: int) -> str:
    return "&#9679;" * n + "&#9675;" * (5 - n)


def formula(text: str) -> str:
    return SUB.sub(r"\1<sub>\2</sub>", text)


def answer_html(short: str) -> str:
    """Turns the agents' line markup into HTML."""
    out: list[str] = []
    rows: list[list[str]] = []

    def flush_table():
        if not rows:
            return
        head, *body = rows
        cells = "".join(f"<th>{c}</th>" for c in head)
        html = f"<table><tr>{cells}</tr>"
        for r in body:
            html += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        out.append(html + "</table>")
        rows.clear()

    for raw in (short or "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("|"):
            rows.append([formula(H.escape(c.strip()))
                         for c in line.strip("|").split("|")])
            continue
        flush_table()
        if line.startswith("F:"):
            out.append(f'<div class="frm">{formula(H.escape(line[2:].strip()))}</div>')
        elif line.startswith("- "):
            out.append(f'<div class="bul">&ndash; '
                       f'{formula(H.escape(line[2:].strip()))}</div>')
        elif line.lower().startswith("note:"):
            out.append(f'<div class="note"><b>Note:</b> '
                       f'{formula(H.escape(line[5:].strip()))}</div>')
        else:
            out.append(f'<p>{formula(H.escape(line))}</p>')
    flush_table()
    return "".join(out)


def block(q, nr, short):
    out = []
    typ = {"open": "open question", "mc": "multiple choice",
           "cloze": "fill in the term"}[q["type"]]
    if q.get("recall"):
        hot = " &middot; VERY FREQUENT" if q.get("hot") else ""
        out.append(f'<div class="meta"><b>Q{nr} &middot; {dots(5)} &middot; PAST EXAM '
                   f'&mdash; {H.escape(q.get("exam", ""))} &middot; asked '
                   f'{int(q.get("count", 1))}&times;{hot}</b></div>')
    else:
        out.append(f'<div class="meta">Q{nr} &middot; {dots(q["score"])} &middot; '
                   f'{typ} &middot; slide {q["slide"]}</div>')

    out.append(f'<div class="q"><b>{H.escape(q["prompt"])}</b></div>')

    if q.get("figure"):
        out.append(f'<div class="fig">&#9654; <b>Figure F{q["fignum"]}</b> at the end '
                   f'&middot; slide {q["slide"]}</div>')

    if q["type"] == "mc":
        for i, o in enumerate(q["options"]):
            mark = "<b>&#9654;</b> " if i in q["correct"] else "&nbsp;&nbsp;&nbsp;"
            out.append(f'<div class="opt">{mark}{chr(97+i)}) {H.escape(o)}</div>')

    out.append(f'<div class="a">{answer_html(short)}</div>')
    return "".join(out)


def build_html(sel, answers):
    n_past = sum(1 for q in sel if q.get("recall"))
    n_sec = len({(q["chapter"], q.get("section")) for q in sel if q.get("section")})
    parts = [
        '<div class="eyebrow">SMART ENERGY INFRASTRUCTURE &middot; KIT &middot; '
        'WINTER TERM 2025/26</div>',
        "<h1>Exam drill &mdash; compact</h1>",
        f'<p class="lead">{len(sel)} questions, answered the way you would answer them '
        f'under time pressure: short, in plain language, with every number that earns '
        f'a mark. All {n_past} questions that provably came up in an earlier exam are '
        f'included and marked <b>PAST EXAM</b>.</p>',
        f'<p class="key"><b>Coverage.</b> All {n_sec} sections of the lecture are '
        'represented, across all 16 chapters. Nothing is left out entirely.</p>',
        f'<p class="key"><b>The relevance score.</b> {dots(5)} came up in a past exam '
        f'or is a direct variant &middot; {dots(4)} sits on a slide a past exam touched, '
        f'or is a core calculation, definition or figure &middot; {dots(3)} solid '
        f'examinable content &middot; {dots(2)} secondary detail.</p>',
        '<p class="key"><b>Reading it.</b> The question is in bold, the answer follows '
        'in normal weight. Formulas sit on their own indented line. For multiple choice '
        'the correct option carries a triangle. Figures are collected at the end and '
        'referenced by number.</p>',
        '<p class="small">Printed in black and white on purpose. Slide numbers refer to '
        'the merged 736-page script in the repository Wink722/SmartEnergySystems, where '
        'the same questions live in the app with longer explanations and spaced '
        'repetition.</p>',
    ]
    cur, nr = None, 0
    for q in sel:
        if q["chapter"] != cur:
            cur = q["chapter"]
            parts.append(f'<h2>{cur} &middot; {H.escape(q["chapter_title"])}</h2>')
        nr += 1
        parts.append(block(q, nr, answers.get(q["id"], "")))
    return "".join(parts)


def append_figures(sel):
    """Drawn directly rather than flowed: the layout engine squeezes an inline
    image into whatever space is left at the bottom of a page and drops it when
    there is too little."""
    figs = [q for q in sel if q.get("figure")]
    if not figs:
        return
    doc = fitz.open(OUT)
    mb = fitz.paper_rect("a4")
    slots = [fitz.Rect(70, 112, mb.x1 - 70, 434), fitz.Rect(70, 476, mb.x1 - 70, 798)]
    page = None
    for i, q in enumerate(figs):
        if i % 2 == 0:
            page = doc.new_page(width=mb.x1, height=mb.y1)
            if i == 0:
                page.insert_text((70, 66), "Figures", fontsize=20)
                page.insert_text((70, 84), "For the drawing, labelling and "
                                 "table-reading questions.", fontsize=8)
        box = slots[i % 2]
        cap = (f"F{q['fignum']} · Q{q['qnum']} · slide {q['slide']} — "
               f"{q.get('slide_title','')}")
        page.insert_text((box.x0, box.y0 - 8), cap[:105], fontsize=8)
        img = os.path.join(PNG, f"{q['slide']:04d}.png")
        pix = fitz.Pixmap(img)
        scale = min(box.width / pix.width, box.height / pix.height)
        target = fitz.Rect(box.x0, box.y0,
                           box.x0 + pix.width * scale, box.y0 + pix.height * scale)
        page.insert_image(target, filename=img)
        page.draw_rect(target, color=(0, 0, 0), width=0.4)
    doc.saveIncr()
    doc.close()


def main() -> None:
    sel = json.load(open(SEL, encoding="utf-8"))
    answers = {a["id"]: a["short"] for a in json.load(open(ANS, encoding="utf-8"))}
    missing = [q["id"] for q in sel if q["id"] not in answers]
    if missing:
        raise SystemExit(f"{len(missing)} Fragen ohne Kurzantwort: {missing[:8]}")

    n = 0
    for i, q in enumerate(sel, 1):
        q["qnum"] = i
        if q.get("figure"):
            n += 1
            q["fignum"] = n

    mediabox = fitz.paper_rect("a4")
    where = mediabox + (52, 48, -52, -52)
    writer = fitz.DocumentWriter(OUT)
    story = fitz.Story(build_html(sel, answers), user_css=CSS)
    more, pages = 1, 0
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
        pages += 1
        if pages > 140:
            break
    writer.close()

    append_figures(sel)

    doc = fitz.open(OUT)
    for i, page in enumerate(doc):
        page.insert_text((52, 812), "Exam drill · compact · Smart Energy Infrastructure",
                         fontsize=7)
        page.insert_text((505, 812), f"{i + 1} / {doc.page_count}", fontsize=7)
    doc.set_metadata({"title": "Exam drill – compact, print version",
                      "author": "Smart Energy Infrastructure, KIT WiSe 2025/26"})
    doc.save(OUT, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    print(f"{len(sel)} Fragen -> {doc.page_count} Seiten -> {OUT}")
    doc.close()


if __name__ == "__main__":
    main()
