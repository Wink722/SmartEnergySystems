"""Home: greeting, daily goal, progress, recommendation for the next step."""

from __future__ import annotations

import html
from datetime import datetime

import streamlit as st

from . import content, srs, storage, ui


def greeting(name: str) -> str:
    hour = datetime.now().hour
    part = ("Good morning" if hour < 11 else
            "Hello" if hour < 17 else
            "Good evening" if hour < 22 else "Still up")
    return f"{part}, {name}" if name else part


def render(p: dict) -> None:
    skipped = p.get("skipped") or {}
    questions = [q for q in content.load_questions() if q["id"] not in skipped]
    chapters = content.chapters()
    units = content.build_units()
    all_ids = [q["id"] for q in questions]

    c = srs.counts(all_ids, p["cards"])
    goal = int(p.get("goal", 60))
    today = storage.day_entry(p)
    done_today = today.get("answered", 0)
    streak = storage.streak_value(p)
    left = storage.days_left(p)
    know = srs.mastery(all_ids, p["cards"])

    total_slides = sum(len(u["slides"]) for u in units)
    learned = sum(1 for u in units for s in u["slides"] if str(s) in p["learned"])

    sub = ("Your study app for “Smart Energy Infrastructure”. New here? Start with "
           "Past exams on the left – those questions provably came up – and then work "
           "through the material in Study.")
    if left is not None and left >= 0:
        tail = (f"{done_today} question{'s' if done_today != 1 else ''} today already "
                "– keep going." if done_today else "Let’s get started.")
        sub = f"{left} day{'s' if left != 1 else ''} until the exam. {tail}"
    ui.hero("Smart Energy Infrastructure", greeting(p.get("name", "")), sub)

    # --------------------------------------------------------- key figures
    items = [
        (f"{done_today}", "answered today", f"daily goal {goal}"),
        (f"{int(know*100)} %", "material consolidated", f"{len(all_ids)} questions in total"),
        (f"{learned}", "slides studied", f"of {total_slides}"),
        (f"{streak}", "day streak", f"best {p['streak'].get('best', 0)}"),
    ]
    if left is not None:
        items.insert(0, (str(max(left, 0)), "days to the exam", p.get("exam_date", "")))
    ui.stat_grid(items)
    ui.spacer("s")
    ui.bar(done_today / max(1, goal))
    note = ("Daily goal reached – everything else is a bonus."
            if done_today >= goal else
            f"{goal - done_today} questions to go until the daily goal.")
    st.markdown(f'<div class="small muted" style="margin-top:.4rem">{note}</div>',
                unsafe_allow_html=True)
    ui.spacer()

    # ------------------------------------------------------ recommendation
    next_unit = None
    for u in units:
        read = sum(1 for s in u["slides"] if str(s) in p["learned"]) / max(1, len(u["slides"]))
        if read < 0.999:
            next_unit = u
            break

    # The questions from the memory protocols take priority over everything else.
    recall_ids = [q["id"] for q in content.load_pastexams()]
    recall_open = [i for i in recall_ids if not p["cards"].get(i, {}).get("seen")]

    if recall_ids and len(recall_open) > len(recall_ids) * 0.2:
        title = f"{len(recall_open)} past-exam questions you have not practised yet"
        body = (f"{len(recall_ids)} questions from the memory protocols and the official "
                "example – these really came up in earlier exams, several of them more "
                "than once. Starting there pays off most.")
        target, label = "Past exams", "Open Past exams"
    elif c["due"] >= 12 and learned > 0:
        title = f"{c['due']} repetitions are due"
        body = ("Repeat first – that keeps what you have already learnt in place. "
                "After that you can take on new material.")
        target, label = "Practice", "Start repeating"
    elif next_unit:
        title = f"Continue with: {next_unit['label']}"
        body = (f"Chapter {next_unit['chapter']} · {len(next_unit['slides'])} slides, "
                f"{len(next_unit['questions'])} questions. Look at the slide and read the "
                "key points, then answer the questions on it right away.")
        target, label = "Study", "Open Study"
    else:
        title = "Worked through once, all of it"
        body = ("You have seen the complete material. From here, repetition and mock "
                "exams are what count.")
        target, label = "Mock exam", "Start a mock exam"

    st.markdown(
        f"""<div class="card pad-lg rise" style="border-color:var(--accent)">
        <div class="eyebrow" style="color:var(--accent)">Your next step</div>
        <h2 style="margin:.4rem 0 .45rem;font-size:1.5rem">{html.escape(title)}</h2>
        <p class="small muted" style="line-height:1.65;max-width:62ch;margin:0">
        {html.escape(body)}</p></div>""",
        unsafe_allow_html=True)
    ui.spacer("s")
    cols = st.columns([1.4, 1.4, 1.4, 2])
    with cols[0]:
        if st.button(label, type="primary", key="go_next"):
            st.session_state["view"] = target
            st.rerun()
    with cols[1]:
        if st.button("Quick round", key="go_quick",
                     help="15 due questions from across all chapters"):
            queue = srs.build_queue(all_ids, p["cards"], limit=15)
            st.session_state["pr_queue"] = queue
            st.session_state["pr_pos"] = 0
            st.session_state["pr_run"] = {"right": 0, "n": 0, "streak": 0}
            st.session_state["view"] = "Practice"
            st.rerun()
    with cols[2]:
        if st.button("Practise the shaky ones", key="go_weak",
                     disabled=c["shaky"] == 0,
                     help="Only the questions you got wrong last time"):
            weak = [i for i in all_ids if srs.status(p["cards"].get(i)) == "shaky"][:20]
            st.session_state["pr_queue"] = weak
            st.session_state["pr_pos"] = 0
            st.session_state["pr_run"] = {"right": 0, "n": 0, "streak": 0}
            st.session_state["view"] = "Practice"
            st.rerun()

    ui.spacer()

    # -------------------------------------------------------------- blocks
    ui.section_title(f"The {len(chapters)} chapters",
                     f"{len(all_ids)} questions · {total_slides} slides")
    for block in content.blocks():
        rows = ""
        for ch in block["chapters"]:
            ids = [q for u in ch["units"] for q in u["questions"]]
            pages = [s for u in ch["units"] for s in u["slides"]]
            read = sum(1 for s in pages if str(s) in p["learned"]) / max(1, len(pages))
            m = srs.mastery(ids, p["cards"])
            dot = "on" if read >= .999 else ("half" if read > 0 else "off")
            rows += (
                f'<div class="rowline"><span class="dot {dot}"></span>'
                f'<span class="nm" style="margin-left:.65rem"><b>{ch["num"]} · '
                f'{html.escape(ch["title"])}</b><span class="small muted"> · '
                f'{len(pages)} slides, {len(ids)} questions</span></span>'
                f'<span class="small muted">{int(read*100)} % read</span>'
                f'{ui.chip(f"{int(m*100)} %", "ok" if m > .6 else "warn" if m > .25 else "")}'
                f'</div>')
        st.markdown(
            f'<div class="card"><div class="eyebrow" style="margin-bottom:.35rem">'
            f'{html.escape(block["name"])}</div>{rows}</div>',
            unsafe_allow_html=True)

    ui.spacer()
    st.markdown(
        """<div class="card"><div class="eyebrow">How this app works</div>
        <div class="lk-point"><span class="n">1</span><span><b>Past exams</b> – every
        question from the memory protocols and the official example, with how often it
        was asked and a model answer built from the slides. The highest-yield hour you
        can spend.</span></div>
        <div class="lk-point"><span class="n">2</span><span><b>Study</b> – chapter by
        chapter through the original slides, key points beside each one and the matching
        questions right underneath.</span></div>
        <div class="lk-point"><span class="n">3</span><span><b>Practice</b> – the app
        remembers what stuck and what did not. Wrong answers come back within minutes,
        solid ones only after a day or two.</span></div>
        <div class="lk-point"><span class="n">4</span><span><b>Mock exam</b> – 90 minutes
        under time pressure with a breakdown by chapter, as soon as a chapter is
        standing.</span></div>
        <div class="lk-point"><span class="n">5</span><span><b>Script &amp; glossary</b> –
        to look things up: every question points back to the slide it came from.</span></div>
        </div>""",
        unsafe_allow_html=True)
