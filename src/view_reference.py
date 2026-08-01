"""Script (PDF), glossary with full-text search, statistics and settings."""

from __future__ import annotations

import html
from datetime import date, timedelta

import streamlit as st

from . import content, srs, storage, ui


# ================================================================= Script

def render_script(p: dict) -> None:
    ui.hero("Script", "The original slides",
            "The complete lecture as one PDF – page through it freely, jump to a "
            "chapter or download the script.")

    slides = content.load_slides()
    chapters = content.chapters()
    total = len(slides)

    if "pdf_page" not in st.session_state:
        st.session_state["pdf_page"] = 2

    ui.section_title("Jump to a chapter")
    # Sixteen chapters do not fit into one row of buttons - eight per row.
    for start in range(0, len(chapters), 8):
        row = chapters[start:start + 8]
        cols = st.columns(8)
        for col, ch in zip(cols, row):
            with col:
                first = min(s for u in ch["units"] for s in u["slides"])
                if st.button(f"Ch {ch['num']}", key=f"jump_{ch['num']}",
                             help=ch["title"]):
                    st.session_state["pdf_page"] = first
                    st.rerun()

    ui.spacer("s")
    nav = st.columns([1, 1, 2.4, 1.4])
    page = int(st.session_state["pdf_page"])
    with nav[0]:
        if st.button("←", key="pdf_prev", disabled=page <= 1):
            st.session_state["pdf_page"] = page - 1
            st.rerun()
    with nav[1]:
        if st.button("→", key="pdf_next", disabled=page >= total):
            st.session_state["pdf_page"] = page + 1
            st.rerun()
    with nav[2]:
        new = st.slider("Page", 1, total, page, label_visibility="collapsed")
        if new != page:
            st.session_state["pdf_page"] = new
            st.rerun()
    with nav[3]:
        st.markdown(f'<div class="small muted center" style="padding-top:.45rem">'
                    f'page {page} of {total}</div>', unsafe_allow_html=True)

    s = slides.get(page, {})
    if s.get("chapter"):
        st.markdown(
            f'<div class="small muted" style="margin:.5rem 0">'
            f'Chapter {s["chapter"]} · {html.escape(s.get("part") or "")}'
            f'{" · " + html.escape(s["section"]) if s.get("section") else ""}</div>',
            unsafe_allow_html=True)

    ui.show_slide(page, caption="", dpi=200)

    ui.spacer("s")
    dl = st.columns([1.4, 1.4, 3])
    with dl[0]:
        ui.slide_download(page)
    with dl[1]:
        try:
            st.download_button("Whole PDF", ui.PDF_PATH.read_bytes(),
                               file_name="smart_energy_systems.pdf",
                               mime="application/pdf", key="dl_pdf")
        except Exception:
            pass

    qids = content.questions_by_slide().get(page, [])
    if qids:
        index = content.question_index()
        ui.spacer()
        with st.expander(f"{len(qids)} questions on this slide"):
            for qid in qids:
                q = index[qid]
                card = p["cards"].get(qid, {})
                box = int(card.get("box", 0)) if card.get("seen") else -1
                lab = ("not practised yet" if box < 0 else f"box {box} of {srs.MAX_BOX}")
                st.markdown(
                    f"""<div style="padding:.6rem 0;border-bottom:1px solid var(--line)">
                    <div class="small" style="font-weight:600">{html.escape(q['prompt'])}</div>
                    <div class="small muted" style="margin-top:.3rem;line-height:1.6">
                    {html.escape(q['solution'])}</div>
                    <div class="small" style="margin-top:.25rem;color:var(--faint)">{lab}</div>
                    </div>""", unsafe_allow_html=True)


# ===================================================== Glossary and search

def render_glossary(p: dict) -> None:
    ui.hero("Look up", "Glossary & search",
            "Every technical term with a definition and a slide reference – plus a "
            "full-text search across all questions, model answers and slide text.")

    term = st.text_input(
        "Search",
        placeholder="e.g. entry-exit, working gas, merit order, Averch-Johnson, LOHC …",
        label_visibility="collapsed")

    if term.strip():
        hits = content.search(term)
        tabs = st.tabs([f"Questions ({len(hits['questions'])})",
                        f"Slides ({len(hits['slides'])})"])
        with tabs[0]:
            if not hits["questions"]:
                st.markdown('<p class="small muted">No hits.</p>', unsafe_allow_html=True)
            for q in hits["questions"][:30]:
                st.markdown(
                    f"""<div class="gl"><div class="t">{html.escape(q['prompt'])}</div>
                    <div class="d">{html.escape(q['solution'])}</div>
                    <div class="small" style="margin-top:.35rem;color:var(--accent)">
                    Chapter {q['chapter']} · slide {q['slide']}</div></div>""",
                    unsafe_allow_html=True)
        with tabs[1]:
            if not hits["slides"]:
                st.markdown('<p class="small muted">No hits.</p>', unsafe_allow_html=True)
            for s in hits["slides"][:20]:
                with st.expander(f"Slide {s['page']} · {s['title'][:70]}"):
                    ui.show_slide(s["page"])
        return

    entries = content.glossary()
    letters = sorted({e["term"][0].upper() for e in entries})
    chosen = st.multiselect("Filter by chapter",
                            [f"Chapter {c['num']}" for c in content.chapters()],
                            label_visibility="collapsed",
                            placeholder="All chapters")
    if chosen:
        nums = {int(c.split()[1]) for c in chosen}
        entries = [e for e in entries if e["chapter"] in nums]

    st.markdown(f'<div class="small muted">{len(entries)} terms · '
                f'{" · ".join(letters)}</div>', unsafe_allow_html=True)
    ui.spacer("s")

    rows = "".join(
        f"""<div class="gl"><div class="t">{html.escape(e['term'])}</div>
        <div class="d">{html.escape(e['definition'])}</div>
        <div class="small" style="margin-top:.3rem;color:var(--accent)">
        Chapter {e['chapter']} · slide {e['slide']}
        {" · " + html.escape(e['section']) if e['section'] else ""}</div></div>"""
        for e in entries
    )
    st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)


# ============================================================= Statistics

def render_stats(p: dict) -> None:
    skipped = p.get("skipped") or {}
    questions = [q for q in content.load_questions() if q["id"] not in skipped]
    chapters = content.chapters()
    all_ids = [q["id"] for q in questions]
    c = srs.counts(all_ids, p["cards"])
    recall_ids = [q["id"] for q in content.load_pastexams()]

    ui.hero("Statistics", "Where you stand",
            "In black and white: what sits, what wobbles and how much you have got "
            "through in the last few days.")

    total_answers = sum(d.get("answered", 0) for d in p["days"].values())
    total_right = sum(d.get("right", 0) for d in p["days"].values())
    rate = int(round(total_right / total_answers * 100)) if total_answers else 0
    ui.stat_grid([
        (str(total_answers), "answers in total", ""),
        (f"{rate} %", "hit rate", f"{total_right} correct"),
        (f"{int(srs.mastery(all_ids, p['cards'])*100)} %", "material consolidated", ""),
        (f"{int(srs.mastery(recall_ids, p['cards'])*100)} %", "past exams sit",
         f"{len(recall_ids)} past-exam questions"),
        (str(storage.streak_value(p)), "day streak", f"best {p['streak'].get('best',0)}"),
    ])
    if skipped:
        st.markdown(f'<div class="small muted" style="margin-top:.5rem">'
                    f'{len(skipped)} questions are deselected as not exam-relevant and '
                    f'do not count here.</div>', unsafe_allow_html=True)
    ui.spacer()

    left, right = st.columns([1, 1])
    with left:
        st.markdown('<div class="card"><div class="eyebrow">Card status</div>',
                    unsafe_allow_html=True)
        rows = ""
        for label, key, tone in [("sits safely", "solid", "ok"),
                                 ("building up", "learning", "warn"),
                                 ("shaky", "shaky", "bad"),
                                 ("never seen", "new", "")]:
            share = c[key] / max(1, len(all_ids))
            rows += (f'<div class="rowline"><span class="nm">{label}</span>'
                     f'{ui.chip(str(c[key]), tone)}</div>'
                     f'<div class="bar thin" style="margin:.1rem 0 .5rem">'
                     f'<i style="width:{share*100:.1f}%"></i></div>')
        st.markdown(rows + "</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="eyebrow">Last 21 days</div>',
                    unsafe_allow_html=True)
        cells = ""
        for i in range(20, -1, -1):
            day = (date.today() - timedelta(days=i)).isoformat()
            n = p["days"].get(day, {}).get("answered", 0)
            lvl = 0 if n == 0 else (1 if n < 10 else (2 if n < 25 else (3 if n < 50 else 4)))
            cells += f'<i class="l{lvl}" title="{day}: {n}"></i>' if lvl else '<i></i>'
        st.markdown(f'<div class="heat" style="margin-top:.7rem">{cells}</div>',
                    unsafe_allow_html=True)
        recent = [(d, v) for d, v in sorted(p["days"].items())[-5:]]
        rows = "".join(
            f'<div class="rowline"><span class="nm small">{d}</span>'
            f'<span class="small muted">{v.get("answered",0)} questions · '
            f'{v.get("learned",0)} slides</span></div>' for d, v in reversed(recent))
        st.markdown((rows or '<p class="small muted" style="margin-top:.8rem">'
                             'No study days recorded yet.</p>') + "</div>",
                    unsafe_allow_html=True)

    ui.spacer()
    st.markdown('<div class="card"><div class="eyebrow">Progress by chapter</div>',
                unsafe_allow_html=True)
    rows = ""
    for ch in chapters:
        ids = [q for u in ch["units"] for q in u["questions"]]
        pages = [s for u in ch["units"] for s in u["slides"]]
        read = sum(1 for s in pages if str(s) in p["learned"]) / max(1, len(pages))
        know = srs.mastery(ids, p["cards"])
        tone = "ok" if know > .6 else "warn" if know > .25 else "bad"
        rows += (
            f'<div class="rowline"><span class="nm"><b>{ch["num"]} · '
            f'{html.escape(ch["title"])}</b><span class="small muted"> · '
            f'{len(ids)} questions</span></span>'
            f'<span class="small muted">{int(read*100)} % read</span>'
            f'{ui.chip(f"{int(know*100)} % consolidated", tone)}'
            f'</div><div class="bar thin" style="margin:.1rem 0 .55rem">'
            f'<i style="width:{know*100:.1f}%"></i></div>')
    st.markdown(rows + "</div>", unsafe_allow_html=True)


# =============================================================== Settings

def _skipped_panel(p: dict) -> None:
    """Look at the deselected questions and take them back in."""
    skipped = p.get("skipped") or {}
    index = content.question_index()
    with st.expander(f"Deselected as not exam-relevant ({len(skipped)})"):
        st.markdown(
            '<p class="small muted" style="line-height:1.65">These questions no longer '
            'appear in Practice or the mock exam. You can take them back one at a time '
            'or all at once.</p>', unsafe_allow_html=True)
        if not skipped:
            st.markdown('<p class="small muted">You have not deselected any question '
                        'so far.</p>', unsafe_allow_html=True)
            return
        if st.button("Take all of them back", key="unskip_all"):
            p["skipped"] = {}
            storage.touch()
            st.rerun()
        ui.spacer("s")
        for qid in sorted(skipped):
            q = index.get(qid)
            if not q:
                continue
            cols = st.columns([6, 1.6])
            with cols[0]:
                st.markdown(
                    f'<div class="small" style="padding-top:.45rem">'
                    f'<b>Chapter {q["chapter"]} · slide {q["slide"]}</b> · '
                    f'{html.escape(q["prompt"][:100])}</div>', unsafe_allow_html=True)
            with cols[1]:
                if st.button("Take back", key=f"unskip_{qid}"):
                    storage.toggle_skip(p, qid)
                    st.rerun()


def render_settings(p: dict) -> None:
    ui.hero("Settings", "Fine tuning & backup",
            "Exam date, daily goal and – most importantly – the backup of your "
            "progress.")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    cols = st.columns(3)
    with cols[0]:
        name = st.text_input("Name", value=p.get("name", ""), placeholder="Your name")
        if name != p.get("name", ""):
            p["name"] = name
            storage.touch()
    with cols[1]:
        current = None
        if p.get("exam_date"):
            try:
                current = date.fromisoformat(p["exam_date"])
            except ValueError:
                current = None
        exam = st.date_input("Exam date", value=current, format="DD.MM.YYYY")
        iso = exam.isoformat() if exam else ""
        if iso != p.get("exam_date", ""):
            p["exam_date"] = iso
            storage.touch()
    with cols[2]:
        goal = st.number_input("Daily goal (questions)", 10, 300,
                               int(p.get("goal", 60)), step=10)
        if goal != p.get("goal"):
            p["goal"] = int(goal)
            storage.touch()
    st.markdown("</div>", unsafe_allow_html=True)

    ui.spacer()
    st.markdown(
        """<div class="card"><div class="eyebrow">Back up your progress</div>
        <p class="small muted" style="margin-top:.5rem;line-height:1.65">
        Your progress lives in this browser's storage and stays there after you close the
        page. If you switch browser, clear your history or want to carry on from another
        device, download the backup file here and import it there.</p></div>""",
        unsafe_allow_html=True)
    ui.spacer("s")

    cols = st.columns([1.3, 1.3, 2])
    with cols[0]:
        st.download_button("Download backup", storage.export_bytes(p),
                           file_name=f"progress_{date.today().isoformat()}.json",
                           mime="application/json", key="dl_backup")
    with cols[1]:
        if st.button("Save now", key="force_save"):
            storage.touch()
            ui.toast("Progress saved")

    up = st.file_uploader("Import a backup", type=["json"],
                          label_visibility="collapsed")
    if up is not None:
        data = storage.import_payload(up.read().decode("utf-8"))
        if data:
            if st.button("Use this progress", type="primary", key="do_import"):
                st.session_state["progress"] = data
                storage.touch()
                ui.toast("Progress imported")
                st.rerun()
            st.markdown(
                f'<div class="small muted">Contains {len(data["cards"])} practised '
                f'questions, {len(data["learned"])} studied slides, created on '
                f'{html.escape(data.get("created",""))}.</div>', unsafe_allow_html=True)
        else:
            st.error("The file could not be read.")

    ui.spacer()
    _skipped_panel(p)

    ui.spacer()
    with st.expander("Reset your progress"):
        st.markdown('<p class="small muted">Deletes every card, every studied slide and '
                    'all statistics. This cannot be undone.</p>',
                    unsafe_allow_html=True)
        confirm = st.text_input("Type RESET to confirm", key="reset_confirm")
        if st.button("Reset for good", key="do_reset",
                     disabled=confirm.strip().upper() != "RESET"):
            keep = p.get("name", "")
            st.session_state["progress"] = storage.blank(keep)
            storage.touch()
            st.rerun()

    ui.spacer()
    st.markdown(
        """<div class="card"><div class="eyebrow">About this app</div>
        <p class="small muted" style="margin-top:.5rem;line-height:1.7">
        Content: “Smart Energy Infrastructure”, KIT, winter term 2025/26 –
        Dr. Dr. Andrej Pustišek (gas, oil and infrastructure), Dr. Armin Ardone (power
        systems analysis) and Julia Schuler (hydrogen and derivatives), six slide decks
        merged into one continuous script.<br><br>
        All questions and model answers were written from the original slides; every
        question links back to the slide it came from. Where the slides contradict
        themselves or contain an error, the model answer gives the factually correct
        version and says so.</p></div>""",
        unsafe_allow_html=True)
