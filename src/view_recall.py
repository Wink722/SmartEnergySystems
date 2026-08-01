"""Past exams: the questions that provably came up.

Sources are the two memory protocols (winter term 22/23 and 25/26) and the official
example exercise handed out for 25/26. The number behind each question says how often
that topic appeared; some are marked as very frequent. This is the material with the
highest chance of being asked again.
"""

from __future__ import annotations

import html

import streamlit as st

from . import content, qcard, srs, storage, ui

SOURCE = "memory protocols WS 22/23 and WS 25/26, plus the official example exercise"


def _questions() -> list[dict]:
    """Past-exam questions with chapter, sorted by frequency."""
    index = {q["id"]: q for q in content.load_questions()}
    out = [index.get(a["id"], a) for a in content.load_pastexams()]
    return sorted(out, key=lambda q: (-int(q.get("count", 1)), q.get("nr", 0)))


def render(p: dict) -> None:
    items = _questions()
    if not items:
        ui.hero("Past exams", "No questions on file yet",
                "As soon as the protocol questions sit in data/pastexams, they show up "
                "here.")
        return

    if st.session_state.get("rc_queue"):
        _run(p, items)
        return

    ids = [q["id"] for q in items]
    c = srs.counts(ids, p["cards"])
    hot = [q for q in items if q.get("hot")]
    occurrences = sum(int(q.get("count", 1)) for q in items)

    ui.hero("Past exams", "What actually came up",
            f"{len(items)} questions from the memory protocols and the official example, "
            f"{occurrences} appearances in total. If you manage only one thing before the "
            "exam, make it this. Every question has a model answer built from the "
            "lecture slides.")

    ui.stat_grid([
        (str(len(items)), "past-exam questions", "WS 22/23 · WS 25/26 · example"),
        (str(len(hot)), "very frequent", "asked more than once"),
        (f"{int(srs.mastery(ids, p['cards']) * 100)} %", "consolidated", ""),
        (str(c["new"]), "never practised", f"{c['solid']} sit safely"),
    ])
    ui.spacer()

    ui.section_title("Work through them",
                     "Write your answer first, then compare with the model answer")
    cols = st.columns([1.5, 1.5, 1.5, 2])
    with cols[0]:
        if st.button("All, in order", type="primary", key="rc_all",
                     help="Starts with the questions that came up most often"):
            _start(ids)
    with cols[1]:
        if st.button("Only the frequent ones", key="rc_hot", disabled=not hot):
            _start([q["id"] for q in hot])
    with cols[2]:
        open_ids = [q["id"] for q in items
                    if not p["cards"].get(q["id"], {}).get("seen")
                    or srs.status(p["cards"].get(q["id"])) == "shaky"]
        if st.button("Not solid yet", key="rc_open", disabled=not open_ids,
                     help="Everything that is new or did not sit last time"):
            _start(open_ids)

    ui.spacer()
    ui.section_title("All questions with model answers", f"{len(items)} questions")

    exams = sorted({q.get("exam", "") for q in items if q.get("exam")})
    pick_exam = st.multiselect("Exam", exams, label_visibility="collapsed",
                               placeholder="All exams")
    chapters = sorted({q["chapter"] for q in items})
    pick_ch = st.multiselect("Chapter", [f"Chapter {k}" for k in chapters],
                             label_visibility="collapsed", placeholder="All chapters")
    only_hot = st.checkbox("Only the very frequent questions", value=False,
                           key="rc_only_hot")

    shown = items
    if pick_exam:
        shown = [q for q in shown if q.get("exam") in set(pick_exam)]
    if pick_ch:
        nums = {int(w.split()[1]) for w in pick_ch}
        shown = [q for q in shown if q["chapter"] in nums]
    if only_hot:
        shown = [q for q in shown if q.get("hot")]

    for q in shown:
        _entry(q, p)


def _start(ids: list[str]) -> None:
    st.session_state["rc_queue"] = ids
    st.session_state["rc_pos"] = 0
    st.session_state["rc_run"] = {"right": 0, "n": 0}
    st.rerun()


def _entry(q: dict, p: dict) -> None:
    """One past-exam question as an expandable entry with its model answer."""
    card = p["cards"].get(q["id"], {})
    n = int(q.get("count", 1))
    mark = " · very frequent" if q.get("hot") else ""
    short = q["prompt"] if len(q["prompt"]) <= 130 else q["prompt"][:127].rstrip() + "…"
    with st.expander(f"{q.get('nr', '')}. {short}   —   asked {n}×{mark}"):
        chips = qcard.recall_chips(q) + ui.chip("Chapter %d" % q["chapter"])
        if q.get("exam"):
            chips += ui.chip(q["exam"])
        chips += qcard.status_badge(card)
        st.markdown(f'<div class="qmeta" style="margin-bottom:.7rem">{chips}</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div class="acard"><div class="lab">Model answer</div>'
            f'<p style="white-space:pre-wrap">{html.escape(q.get("solution", ""))}</p></div>',
            unsafe_allow_html=True)
        if q.get("note"):
            st.markdown(
                f'<div class="small muted" style="margin-top:.6rem;line-height:1.6">'
                f'<b>Note:</b> {html.escape(q["note"])}</div>', unsafe_allow_html=True)
        if q.get("keywords"):
            kws = "".join(f'<span class="kw">{html.escape(k)}</span>' for k in q["keywords"])
            st.markdown(f'<div style="margin-top:.7rem">{kws}</div>', unsafe_allow_html=True)

        pages = q.get("slides") or []
        if pages:
            ui.spacer("s")
            st.markdown('<div class="eyebrow">The slides behind this answer</div>',
                        unsafe_allow_html=True)
            for page in pages:
                slide = content.load_slides().get(page, {})
                with st.expander(f"Slide {page} · {slide.get('title', '')[:70]}"):
                    ui.show_slide(page)


# ------------------------------------------------------------------- a run

def _run(p: dict, items: list[dict]) -> None:
    queue = st.session_state["rc_queue"]
    pos = int(st.session_state.get("rc_pos", 0))
    index = {q["id"]: q for q in items}

    top = st.columns([1.1, 5, 1.6])
    with top[0]:
        if st.button("← Finish", key="rc_stop"):
            _clear()
            st.rerun()
    with top[2]:
        st.markdown(f'<div class="small muted center" style="padding-top:.45rem">'
                    f'{min(pos + 1, len(queue))} / {len(queue)}</div>',
                    unsafe_allow_html=True)

    if pos >= len(queue):
        run = st.session_state.get("rc_run", {"right": 0, "n": 0})
        rate = int(round(run["right"] / max(1, run["n"]) * 100))
        ui.hero("Done", "Round finished",
                f"{run['n']} past-exam questions answered, {rate} % sat.")
        if run["n"] and run["right"] == run["n"]:
            st.session_state["celebrate"] = "Every past-exam question in this round sat!"
        if st.button("Back to the overview", type="primary", key="rc_back"):
            _clear()
            st.rerun()
        return

    ui.bar(pos / max(1, len(queue)), thin=True)
    ui.spacer("s")

    q = index[queue[pos]]

    def _grade(qid: str, grade: int) -> None:
        card = p["cards"].get(qid) or srs.new_card()
        p["cards"][qid] = srs.review(card, grade)
        storage.record_answer(p, grade == 2)
        run = st.session_state.setdefault("rc_run", {"right": 0, "n": 0})
        run["n"] += 1
        run["right"] += 1 if grade == 2 else 0
        storage.touch()
        qcard.reset(qid)
        st.session_state["rc_pos"] = pos + 1
        st.rerun()

    qcard.render(q, _grade, position=f"Question {pos + 1}")


def _clear() -> None:
    for key in ("rc_queue", "rc_pos", "rc_run"):
        st.session_state.pop(key, None)
