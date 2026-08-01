"""Rendering and evaluation of a single question."""

from __future__ import annotations

import html
from typing import Callable

import streamlit as st

from . import content, grading, srs, storage, ui
from .content import TYPE_LABEL

TONE = {"mc": "", "cloze": "warn", "open": "ok"}


def _state(qid: str, field: str, default=None):
    return st.session_state.get(f"q_{field}_{qid}", default)


def _set(qid: str, field: str, value) -> None:
    st.session_state[f"q_{field}_{qid}"] = value


def reset(qid: str) -> None:
    for field in ("rev", "res", "ans", "sel"):
        st.session_state.pop(f"q_{field}_{qid}", None)


def recall_chips(q: dict) -> str:
    """Marking for questions taken from the memory protocols."""
    if q.get("recall"):
        n = int(q.get("count", 1))
        out = ui.chip(f"Past exam · asked {n}×", "ok")
        if q.get("hot"):
            out += ui.chip("very frequent", "bad")
        return out
    if content.recall_slides().get(q.get("slide")):
        return ui.chip("topic has come up", "warn")
    return ""


def header(q: dict, position: str = "") -> None:
    chips = ui.chip(TYPE_LABEL[q["type"]], TONE.get(q["type"], ""))
    chips += recall_chips(q)
    chips += ui.chip(f"Chapter {q['chapter']}")
    if q.get("section") or q.get("part"):
        chips += ui.chip((q.get("section") or q.get("part"))[:42])
    if position:
        chips += ui.chip(position)
    st.markdown(
        f"""<div class="qcard rise">
        <div class="qmeta">{chips}</div>
        <div class="qtext">{html.escape(q['prompt'])}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def source_link(q: dict, expanded: bool = False) -> None:
    with st.expander(f"See the source · slide {q['slide']} – {q.get('slide_title','')[:50]}",
                     expanded=expanded):
        ui.show_slide(q["slide"])
        ui.slide_download(q["slide"])


def render(q: dict, on_grade: Callable[[str, int], None], *, position: str = "",
           exam_mode: bool = False, show_source: bool = True) -> None:
    """Draws a question with its input, evaluation and grading."""
    qid = q["id"]
    header(q, position)

    if q.get("graphic"):
        st.markdown('<div class="spacer-s"></div>', unsafe_allow_html=True)
        ui.show_slide(q["slide"], caption=f"Slide {q['slide']} · {q.get('slide_title','')}")

    revealed = _state(qid, "rev", False)

    # -------------------------------------------------------------- input
    if q["type"] == "mc":
        options = q["options"]
        idx = st.radio("Choose an answer", range(len(options)),
                       format_func=lambda i: options[i], key=f"q_sel_{qid}",
                       index=None, disabled=revealed, label_visibility="collapsed")
        given = [idx] if idx is not None else []
    elif q["type"] == "cloze":
        given = st.text_input("Enter the term", key=f"q_ans_{qid}",
                              placeholder="Type the term …", disabled=revealed,
                              label_visibility="collapsed")
    else:
        given = st.text_area("Your answer", key=f"q_ans_{qid}", height=132,
                             placeholder="Answer in bullet points or full sentences – "
                                         "the app checks which core terms you used.",
                             disabled=revealed, label_visibility="collapsed")

    # -------------------------------------------------------------- check
    if not revealed:
        cols = st.columns([1, 1, 2])
        with cols[0]:
            if st.button("Check", key=f"chk_{qid}", type="primary"):
                _set(qid, "res", _evaluate(q, given))
                _set(qid, "rev", True)
                st.rerun()
        with cols[1]:
            if st.button("No idea", key=f"dunno_{qid}"):
                _set(qid, "res", _evaluate(q, [] if q["type"] == "mc" else ""))
                _set(qid, "rev", True)
                st.rerun()
        if show_source and not exam_mode:
            st.markdown('<div class="spacer-s"></div>', unsafe_allow_html=True)
            source_link(q)
        return

    # ------------------------------------------------------------- reveal
    res = _state(qid, "res", {}) or {}
    _reveal(q, res)

    if show_source:
        st.markdown('<div class="spacer-s"></div>', unsafe_allow_html=True)
        # On image-heavy slides the figure belongs next to the solution - that
        # is where the content lives that the slide text does not carry.
        source_link(q, expanded=bool(q.get("graphic") or q.get("slide_graphic")))

    if not exam_mode:
        ask_panel(q, res.get("given"))
        skip_control(q)

    st.markdown('<div class="spacer-s"></div>', unsafe_allow_html=True)
    _grade_buttons(q, res, on_grade)


def skip_control(q: dict) -> None:
    """Mark a question as not exam-relevant - it then drops out of practice and exam."""
    if q.get("recall"):
        return  # questions that provably came up stay in
    p = storage.load()
    qid = q["id"]
    off = storage.is_skipped(p, qid)
    cols = st.columns([2.2, 3])
    with cols[0]:
        label = "Put it back in" if off else "Not exam-relevant"
        if st.button(label, key=f"notrel_{qid}",
                     help="Deselected questions no longer appear in Practice or the "
                          "mock exam."):
            storage.toggle_skip(p, qid)
            st.rerun()
    if off:
        with cols[1]:
            st.markdown('<div class="small muted" style="padding-top:.55rem">'
                        'Deselected – it will not come up again.</div>',
                        unsafe_allow_html=True)


# --------------------------------------------------------------- follow-ups

ASK_INTRO = (
    "I am studying for my Smart Energy Infrastructure exam (KIT, winter term 2025/26) "
    "and I am stuck on one question. Please answer briefly and stick to the slide "
    "content below – that is the material being examined. If you add anything that is "
    "not on the slide, say so explicitly."
)


def ask_block(q: dict, answer: str = "") -> str:
    """Ready-made text to paste into a chat with Claude."""
    slide = content.load_slides().get(q["slide"], {})
    text = (slide.get("text") or "").strip()
    lines = [
        ASK_INTRO, "",
        f"Chapter {q.get('chapter')}: {q.get('chapter_title', '')}",
        f"Section: {q.get('section') or q.get('part') or '-'}",
        f"Slide {q.get('slide')}: {slide.get('title', '')}", "",
        "Slide text:",
        text or "(This slide is essentially one figure.)", "",
        f"Question: {q.get('prompt', '')}",
    ]
    if q.get("options"):
        lines.append("Options: " + " | ".join(q["options"]))
        lines.append("Correct: " + ", ".join(q["options"][i] for i in q.get("correct", [])))
    lines.append(f"Model answer: {q.get('solution', '')}")
    if q.get("keywords"):
        lines.append("Core terms: " + ", ".join(q["keywords"]))
    if answer.strip():
        lines += ["", f"My own answer was: {answer.strip()}"]
    lines += ["", "My follow-up question: "]
    return "\n".join(lines)


def ask_panel(q: dict, given=None) -> None:
    """The full question context to copy - for a follow-up in a Claude chat."""
    with st.expander("Ask about this · copy the context for Claude"):
        st.markdown(
            '<p class="small muted" style="line-height:1.65;margin:0 0 .6rem">'
            'Everything a follow-up needs: slide text, question, model answer and your '
            'own answer. Use the copy icon at the top right of the box, paste it into '
            'claude.ai and write your question at the end.</p>',
            unsafe_allow_html=True)
        st.code(ask_block(q, given if isinstance(given, str) else ""), language=None)


def _evaluate(q: dict, given) -> dict:
    if q["type"] == "mc":
        ok = grading.check_mc(list(given), q["correct"])
        return {"kind": "mc", "ok": ok, "given": list(given), "grade": 2 if ok else 0}
    if q["type"] == "cloze":
        ok, best, close = grading.check_cloze(given or "", q["accept"])
        return {"kind": "cloze", "ok": ok, "given": given, "best": best,
                "close": close, "grade": 2 if ok else (1 if close else 0)}
    check = grading.check_keywords(given or "", q.get("keywords", []))
    return {"kind": "open", **check, "given": given,
            "grade": grading.suggest_grade(check["score"]) if (given or "").strip() else 0}


def _reveal(q: dict, res: dict) -> None:
    kind = res.get("kind")

    if kind == "mc":
        correct_txt = " / ".join(q["options"][i] for i in q["correct"])
        if res.get("ok"):
            body = f"<b>Correct.</b> {html.escape(correct_txt)}"
            cls = ""
        else:
            chosen = res.get("given") or []
            picked = q["options"][chosen[0]] if chosen else "no answer"
            body = (f"<b>Not quite.</b> You had: “{html.escape(picked)}”.<br>"
                    f"Correct is: <b>{html.escape(correct_txt)}</b>")
            cls = " miss"
        st.markdown(
            f"""<div class="acard{cls} flip"><div class="lab">Answer</div>
            <p>{body}</p><p style="margin-top:.6rem">{html.escape(q['solution'])}</p></div>""",
            unsafe_allow_html=True,
        )

    elif kind == "cloze":
        accepted = q["accept"][0]
        if res.get("ok"):
            body = f"<b>Correct.</b> The term was: <b>{html.escape(accepted)}</b>"
            cls = ""
        elif res.get("close"):
            body = (f"<b>Almost.</b> The term was: <b>{html.escape(accepted)}</b> – "
                    f"you typed: “{html.escape(str(res.get('given') or ''))}”")
            cls = " miss"
        else:
            body = f"The term was: <b>{html.escape(accepted)}</b>"
            cls = " miss"
        st.markdown(
            f"""<div class="acard{cls} flip"><div class="lab">Answer</div>
            <p>{body}</p><p style="margin-top:.6rem">{html.escape(q['solution'])}</p></div>""",
            unsafe_allow_html=True,
        )

    else:
        hits, misses = res.get("hits", []), res.get("misses", [])
        pct = int(round(res.get("score", 0) * 100))
        kws = "".join(f'<span class="kw hit">{html.escape(k)}</span>' for k in hits)
        kws += "".join(f'<span class="kw mis">{html.escape(k)}</span>' for k in misses)
        cls = "" if res.get("score", 0) >= 0.5 else " miss"
        st.markdown(
            f"""<div class="acard{cls} flip"><div class="lab">Model answer</div>
            <p>{html.escape(q['solution'])}</p></div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="card" style="margin-top:.7rem">
            <div class="eyebrow">Keyword check · {pct}% of the core terms hit</div>
            <div style="margin-top:.6rem">{kws}</div>
            <div class="small muted" style="margin-top:.7rem">
            Green = appeared in your answer · grey = was missing</div></div>""",
            unsafe_allow_html=True,
        )


def _grade_buttons(q: dict, res: dict, on_grade: Callable[[str, int], None]) -> None:
    qid = q["id"]
    if q["type"] in ("mc", "cloze"):
        auto = res.get("grade", 0)
        cols = st.columns([1.4, 1, 1])
        with cols[0]:
            if st.button("Next", key=f"next_{qid}", type="primary"):
                on_grade(qid, auto)
        if auto < 2:
            with cols[1]:
                if st.button("I did know it", key=f"had_{qid}",
                             help="Only a typo – count it as known"):
                    on_grade(qid, 2)
        return

    st.markdown('<div class="eyebrow">How well did your answer sit?</div>',
                unsafe_allow_html=True)
    cols = st.columns(3)
    labels = [("Solid", 2), ("Half", 1), ("Off", 0)]
    suggested = res.get("grade", 0)
    for col, (label, grade) in zip(cols, labels):
        with col:
            if st.button(label, key=f"g{grade}_{qid}",
                         type="primary" if grade == suggested else "secondary"):
                on_grade(qid, grade)


def status_badge(card: dict | None) -> str:
    st_ = srs.status(card)
    return {
        "new": ui.chip("new"),
        "shaky": ui.chip("shaky", "bad"),
        "learning": ui.chip("building", "warn"),
        "solid": ui.chip("solid", "ok"),
    }[st_]
