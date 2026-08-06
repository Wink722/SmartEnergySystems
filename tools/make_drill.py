"""Builds the exam-practice booklet: questions with model answers, scored."""
import html as H
import json
import os

import fitz

R = r"C:\Users\vince\Desktop\Studium\smart Energy Systems\SmartEnergySystems"
SEL = os.path.join(os.path.dirname(__file__), "selection.json")
PNG = os.path.join(R, ".slides_png")
OUT = (r"C:\Users\vince\Desktop\Studium\smart Energy Systems"
       r"\Exam Drill - Questions and Model Answers.pdf")

CSS = """
* { font-family: sans-serif; }
body { font-size: 8.4pt; line-height: 1.3; color: #16181C; }
h1 { font-size: 26pt; color: #3F6B52; margin-bottom: 2pt; line-height: 1.08; }
h2 { font-size: 12pt; color: #FFFFFF; background-color: #3F6B52; padding: 4pt;
     margin-top: 12pt; margin-bottom: 6pt; }
h3 { font-size: 9.5pt; color: #3F6B52; margin-top: 9pt; margin-bottom: 1pt; }
p  { margin-top: 0pt; margin-bottom: 5pt; }
.lead { font-size: 11pt; color: #444; margin-bottom: 9pt; }
.eyebrow { font-size: 7.5pt; color: #6E7178; letter-spacing: 1pt; margin-bottom: 10pt; }
.meta { font-size: 7.5pt; color: #6E7178; margin-bottom: 2pt; }
.past { font-size: 7.5pt; color: #A33A2E; margin-bottom: 2pt; }
.q { font-size: 9pt; margin-bottom: 3pt; }
.a { background-color: #F2EEE8; padding: 5pt; margin-bottom: 7pt; }
.alabel { font-size: 7pt; color: #3F6B52; letter-spacing: 1pt; margin-bottom: 2pt; }
.opt { font-size: 8.5pt; margin-bottom: 1pt; }
.note { font-size: 8pt; color: #9A6216; margin-top: 3pt; }
.box { background-color: #E4EDE6; padding: 7pt; margin-bottom: 8pt; }
.small { font-size: 8pt; color: #6E7178; }
.fig { font-size: 8pt; color: #3F6B52; margin-bottom: 4pt; }
table { font-size: 8pt; }
td { padding: 2pt; }
"""


def stars(n):
    return "&#9679;" * n + "&#9675;" * (5 - n)


_RATIO: dict[int, float] = {}


def fig_ratio(page: int) -> float:
    """height / width of the rendered slide, cached."""
    if page not in _RATIO:
        pix = fitz.Pixmap(os.path.join(PNG, f"{page:04d}.png"))
        _RATIO[page] = pix.height / pix.width
    return _RATIO[page]


def block(q, nr, pad=None):
    out = []
    typ = {"open": "open question", "mc": "multiple choice",
           "cloze": "fill in the term"}[q["type"]]
    if q.get("recall"):
        exam = q.get("exam", "past exam")
        cnt = int(q.get("count", 1))
        hot = " &middot; VERY FREQUENT" if q.get("hot") else ""
        out.append(f'<div class="past"><b>Q{nr} &middot; {stars(5)} &middot; '
                   f'PAST EXAM &mdash; {H.escape(exam)} &middot; asked {cnt}&times;'
                   f'{hot}</b></div>')
    else:
        out.append(f'<div class="meta"><b>Q{nr}</b> &middot; {stars(q["score"])} '
                   f'&middot; {typ} &middot; slide {q["slide"]}</div>')
    out.append(f'<div class="q"><b>{H.escape(q["prompt"])}</b></div>')

    if q.get("figure"):
        # The figures live in an appendix that is drawn directly rather than
        # flowed: the layout engine squeezes an inline image into whatever space
        # is left at the bottom of a page, and drops it entirely when there is
        # too little - one came out 4 pt wide, four vanished.
        out.append(f'<div class="fig">&#9654; Figure F{q["fignum"]} at the end of '
                   f'this booklet &middot; slide {q["slide"]}</div>')

    if q["type"] == "mc":
        for i, o in enumerate(q["options"]):
            mark = "&#9654; " if i in q["correct"] else "&nbsp;&nbsp;&nbsp;"
            out.append(f'<div class="opt">{mark}{chr(97+i)}) {H.escape(o)}</div>')

    sol = H.escape(q.get("solution", "")).replace("\n", "<br/>")
    lab = "MODEL ANSWER"
    if q["type"] == "cloze":
        lab = f'ANSWER: {H.escape(q["accept"][0].upper())}'
    out.append(f'<div class="a"><div class="alabel">{lab}</div>{sol}')
    if q.get("note"):
        out.append(f'<div class="note"><b>Note:</b> {H.escape(q["note"])}</div>')
    out.append("</div>")
    return "".join(out)


def build_html(sel, pad=None):
    n_past = sum(1 for q in sel if q.get("recall"))
    parts = [
        '<div class="eyebrow">SMART ENERGY INFRASTRUCTURE &middot; KIT &middot; '
        'WINTER TERM 2025/26</div>',
        "<h1>Exam drill</h1>",
        f'<p class="lead">{len(sel)} questions with model answers, written from the '
        f'lecture slides. All {n_past} questions that provably came up in an earlier '
        'exam are included and marked in red.</p>',
        '<div class="box"><b>How to read the score.</b> Every question carries a '
        f'relevance score from {stars(2)} to {stars(5)}.<br/>'
        f'{stars(5)} &mdash; came up in a past exam, or is a direct variant of one. '
        'Learn these first.<br/>'
        f'{stars(4)} &mdash; sits on a slide a past exam touched, or is a core '
        'calculation, definition or figure of a heavily examined section.<br/>'
        f'{stars(3)} &mdash; solid examinable content.<br/>'
        f'{stars(2)} &mdash; secondary detail, worth a look once the rest sits.'
        "</div>",
        '<div class="box"><b>How the questions were chosen.</b> Weighted towards what '
        'the memory protocols show &mdash; calculations, sketches, "name and explain", '
        'comparisons &mdash; but every one of the 16 chapters is represented, so nothing '
        'drops out entirely. The multiple-choice options are shuffled; the correct one '
        'is marked with a triangle.</div>',
        '<p class="small">Slide numbers refer to the merged script (736 pages) in the '
        'repository Wink722/SmartEnergySystems, where every question also lives in the '
        'app with spaced repetition.</p>',
    ]
    cur = None
    nr = 0
    for q in sel:
        if q["chapter"] != cur:
            cur = q["chapter"]
            parts.append(f'<h2>Chapter {cur} &middot; {H.escape(q["chapter_title"])}'
                         f' &nbsp;&mdash;&nbsp; {H.escape(q["block"])}</h2>')
        nr += 1
        parts.append(block(q, nr, pad))
    return "".join(parts)


def append_figures(sel):
    """Draws the figure appendix directly - two per page, always full width."""
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
                page.insert_text((70, 66), "Figures", fontsize=20,
                                 color=(0.247, 0.42, 0.322))
                page.insert_text((70, 82),
                                 "For the drawing, labelling and table-reading "
                                 "questions. Referenced from the question by number.",
                                 fontsize=8, color=(0.43, 0.44, 0.47))
        box = slots[i % 2]
        cap = (f"F{q['fignum']} · Q{q['qnum']} · slide {q['slide']} — "
               f"{q.get('slide_title','')}")
        page.insert_text((box.x0, box.y0 - 8), cap[:105], fontsize=8,
                         color=(0.247, 0.42, 0.322))
        img = os.path.join(PNG, f"{q['slide']:04d}.png")
        pix = fitz.Pixmap(img)
        avail = fitz.Rect(box.x0, box.y0, box.x1, box.y1)
        scale = min(avail.width / pix.width, avail.height / pix.height)
        w, h = pix.width * scale, pix.height * scale
        target = fitz.Rect(avail.x0, avail.y0, avail.x0 + w, avail.y0 + h)
        page.insert_image(target, filename=img)
        page.draw_rect(target, color=(0.85, 0.82, 0.78), width=0.5)
    doc.saveIncr()
    doc.close()


def render(sel, pad):
    mediabox = fitz.paper_rect("a4")
    where = mediabox + (52, 48, -52, -52)
    writer = fitz.DocumentWriter(OUT)
    story = fitz.Story(build_html(sel, pad), user_css=CSS, archive=fitz.Archive(PNG))
    more, n = 1, 0
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
        n += 1
        if n > 120:
            break
    writer.close()


def main():
    sel = json.load(open(SEL, encoding="utf-8"))
    n = 0
    for i, q in enumerate(sel, 1):
        q["qnum"] = i
        if q.get("figure"):
            n += 1
            q["fignum"] = n

    render(sel, None)
    append_figures(sel)

    doc = fitz.open(OUT)
    for i, page in enumerate(doc):
        page.insert_text((52, 810), "Exam drill · Smart Energy Infrastructure",
                         fontsize=7, color=(0.62, 0.62, 0.62))
        page.insert_text((505, 810), f"{i + 1} / {doc.page_count}",
                         fontsize=7, color=(0.62, 0.62, 0.62))
    doc.set_metadata({"title": "Exam drill â€“ questions and model answers",
                      "author": "Smart Energy Infrastructure, KIT WiSe 2025/26"})
    doc.save(OUT, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    pages = doc.page_count
    doc.close()
    print(f"{len(sel)} Fragen -> {pages} Seiten")


if __name__ == "__main__":
    main()
