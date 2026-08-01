"""Study mode: chapter → section → slide by slide, then the matching questions."""

from __future__ import annotations

import html

import streamlit as st

from . import content, qcard, srs, storage, ui


def _units_flat() -> list[dict]:
    return content.build_units()


def _unit_progress(unit: dict, p: dict) -> tuple[float, float]:
    learned = sum(1 for s in unit["slides"] if str(s) in p["learned"])
    read = learned / max(1, len(unit["slides"]))
    know = srs.mastery(unit["questions"], p["cards"])
    return read, know


def _key_points(page: int) -> list[str]:
    """Key points of a slide - taken from the model answers of its questions."""
    qs_by_slide = content.questions_by_slide()
    index = content.question_index()
    points: list[str] = []
    for qid in qs_by_slide.get(page, []):
        q = index[qid]
        if q.get("recall"):
            continue  # the long past-exam answers would blow up the key points
        sol = q.get("solution", "").strip()
        if sol and sol not in points:
            points.append(sol)
    return points


def render(p: dict) -> None:
    units = _units_flat()
    chapters = content.chapters()

    if st.session_state.get("learn_unit"):
        _render_unit(p, st.session_state["learn_unit"])
        return

    ui.hero("Study", "Build the material up",
            "This is where you go through the material slide by slide: the original "
            "slide, its key points in plain language – and the questions on it right "
            "afterwards. Understand first, then get tested.")

    total_slides = sum(len(u["slides"]) for u in units)
    learned = sum(1 for u in units for s in u["slides"] if str(s) in p["learned"])
    ui.stat_grid([
        (f"{learned}", "slides worked through", f"of {total_slides}"),
        (f"{int(round(learned / max(1, total_slides) * 100))} %", "material seen", ""),
        (f"{len(chapters)}", "chapters", "of the lecture"),
    ])
    ui.spacer()

    nxt = _next_unit(units, p)
    if nxt:
        st.markdown(
            f"""<div class="card pad-lg rise" style="border-color:var(--accent)">
            <div class="eyebrow" style="color:var(--accent)">Pick up here</div>
            <div class="lk-title" style="margin-top:.35rem">
            Chapter {nxt['chapter']} · {html.escape(nxt['label'])}</div>
            <div class="small muted" style="margin-top:.35rem">
            {len(nxt['slides'])} slides · {len(nxt['questions'])} questions</div></div>""",
            unsafe_allow_html=True,
        )
        if st.button("Start the section", type="primary", key="cont_unit"):
            st.session_state["learn_unit"] = nxt["key"]
            st.session_state["learn_pos"] = _first_unlearned(nxt, p)
            st.rerun()
        ui.spacer()

    current_block = None
    for ch in chapters:
        if ch["block"] != current_block:
            current_block = ch["block"]
            ui.section_title(current_block)
        read_all, know_all = _chapter_progress(ch, p)
        with st.expander(
            f"Chapter {ch['num']} · {ch['title']}   —   "
            f"{int(read_all*100)} % read, {int(know_all*100)} % consolidated",
            expanded=(nxt is not None and ch["num"] == nxt["chapter"]),
        ):
            st.markdown(
                f"""<p class="small muted" style="line-height:1.65">{html.escape(ch['intro'])}</p>
                <div class="small" style="margin:.5rem 0 1rem;color:var(--accent)">
                <b>The thread:</b> {html.escape(ch['thread'])}</div>""",
                unsafe_allow_html=True,
            )
            for unit in ch["units"]:
                read, know = _unit_progress(unit, p)
                dot = "on" if read >= 0.999 else ("half" if read > 0 else "off")
                cols = st.columns([6, 2.2, 1.6])
                with cols[0]:
                    st.markdown(
                        f"""<div class="rowline"><span class="dot {dot}"></span>
                        <span class="nm" style="margin-left:.6rem"><b>{html.escape(unit['label'])}</b>
                        <span class="small muted"> · {len(unit['slides'])} slides ·
                        {len(unit['questions'])} questions</span></span></div>""",
                        unsafe_allow_html=True,
                    )
                with cols[1]:
                    ui.bar(read, thin=True)
                    st.markdown(
                        f'<div class="small muted" style="margin-top:.25rem">'
                        f'{int(read*100)} % read</div>', unsafe_allow_html=True)
                with cols[2]:
                    if st.button("Open", key=f"open_{unit['key']}"):
                        st.session_state["learn_unit"] = unit["key"]
                        st.session_state["learn_pos"] = _first_unlearned(unit, p)
                        st.rerun()


def _chapter_progress(ch: dict, p: dict) -> tuple[float, float]:
    slides = [s for u in ch["units"] for s in u["slides"]]
    qs = [q for u in ch["units"] for q in u["questions"]]
    read = sum(1 for s in slides if str(s) in p["learned"]) / max(1, len(slides))
    return read, srs.mastery(qs, p["cards"])


def _first_unlearned(unit: dict, p: dict) -> int:
    for i, page in enumerate(unit["slides"]):
        if str(page) not in p["learned"]:
            return i
    return 0


def _next_unit(units: list[dict], p: dict) -> dict | None:
    for unit in units:
        read, _ = _unit_progress(unit, p)
        if read < 0.999:
            return unit
    return None


# ----------------------------------------------------------------- section

def _render_unit(p: dict, key: str) -> None:
    units = {u["key"]: u for u in _units_flat()}
    unit = units.get(key)
    if not unit:
        st.session_state.pop("learn_unit", None)
        st.rerun()
        return

    pos = int(st.session_state.get("learn_pos", 0))
    pos = max(0, min(pos, len(unit["slides"]) - 1))
    page = unit["slides"][pos]
    slides = content.load_slides()
    slide = slides[page]

    top = st.columns([1.1, 5, 1.6])
    with top[0]:
        if st.button("← Overview", key="back_units"):
            st.session_state.pop("learn_unit", None)
            st.rerun()
    with top[2]:
        st.markdown(
            f'<div class="small muted center" style="padding-top:.45rem">'
            f'{pos+1} / {len(unit["slides"])}</div>', unsafe_allow_html=True)

    st.markdown(
        f"""<div class="hero fade" style="margin-top:.6rem;margin-bottom:1rem">
        <div class="eyebrow">Chapter {unit['chapter']} · {html.escape(unit['part'])}</div>
        <h1 style="font-size:1.9rem">{html.escape(unit['label'])}</h1></div>""",
        unsafe_allow_html=True,
    )
    ui.bar((pos + 1) / len(unit["slides"]), thin=True)
    ui.spacer("s")

    if unit["intro"] and pos == 0:
        st.markdown(
            f"""<div class="acard fade" style="margin-bottom:1.1rem">
            <div class="lab">What is this about?</div>
            <p>{html.escape(unit['intro'])}</p></div>""",
            unsafe_allow_html=True,
        )

    # ------------------------------------------------------------ study card
    came_up = content.recall_slides().get(page, [])
    mark = ""
    if came_up:
        n = sum(int(a.get("count", 1)) for a in content.load_pastexams()
                if a["id"] in came_up)
        mark = ('<div style="margin-top:.5rem">'
                + ui.chip(f"This slide carries {n} past-exam question"
                          f"{'s' if n != 1 else ''}", "ok") + "</div>")
    st.markdown(
        f"""<div class="card pad-lg rise">
        <div class="eyebrow">Slide {page}</div>
        <div class="lk-title">{html.escape(slide['title'] or 'Slide')}</div>{mark}""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    left, right = st.columns([1.05, 1])
    with left:
        ui.show_slide(page, caption=f"Original slide {page}")
    with right:
        points = _key_points(page)
        if points:
            rows = "".join(
                f'<div class="lk-point"><span class="n">{i+1}</span>'
                f'<span>{html.escape(pt)}</span></div>'
                for i, pt in enumerate(points)
            )
            st.markdown(
                f"""<div class="card fade"><div class="eyebrow">What to take away</div>
                <div style="margin-top:.6rem">{rows}</div></div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div class="card fade"><div class="eyebrow">Slide content</div>
                <p class="small" style="white-space:pre-wrap;line-height:1.6;margin-top:.5rem">
                {html.escape(slide['text'][:900])}</p></div>""",
                unsafe_allow_html=True,
            )

    ui.spacer()

    # ------------------------------------------------------ questions on it
    skipped = p.get("skipped") or {}
    qids = [i for i in content.questions_by_slide().get(page, []) if i not in skipped]
    index = content.question_index()
    if qids:
        done_key = f"learn_q_{page}"
        answered = st.session_state.setdefault(done_key, set())
        ui.section_title("Test yourself right away",
                         f"{len(answered)} of {len(qids)} answered")

        for qid in qids:
            q = index[qid]
            if qid in answered:
                card = p["cards"].get(qid, {})
                st.markdown(
                    f"""<div class="card" style="padding:.85rem 1.1rem">
                    <div style="display:flex;justify-content:space-between;gap:1rem;
                    align-items:center"><span class="small">{html.escape(q['prompt'][:110])}</span>
                    {qcard.status_badge(card)}</div></div>""",
                    unsafe_allow_html=True,
                )
                continue

            def _grade(gid: str, grade: int, _page=page, _done=done_key) -> None:
                _apply_grade(p, gid, grade)
                st.session_state[_done].add(gid)
                qcard.reset(gid)
                st.rerun()

            qcard.render(q, _grade, show_source=False)
            break  # only ever show the next open question

    ui.spacer()

    # ---------------------------------------------------------- navigation
    nav = st.columns([1, 1, 1.4])
    with nav[0]:
        if st.button("← Back", key="prev_slide", disabled=pos == 0):
            st.session_state["learn_pos"] = pos - 1
            st.rerun()
    with nav[1]:
        last = pos >= len(unit["slides"]) - 1
        if st.button("Next →" if not last else "Finish the section",
                     key="next_slide", type="primary"):
            was_new = storage.record_learned(p, page)
            storage.touch()
            if last:
                st.session_state["learn_done_unit"] = unit["key"]
                st.session_state.pop("learn_unit", None)
            else:
                st.session_state["learn_pos"] = pos + 1
            if was_new and (len(p["learned"]) % 25 == 0):
                st.session_state["celebrate"] = f"{len(p['learned'])} slides done!"
            st.rerun()
    with nav[2]:
        marked = str(page) in p["learned"]
        st.markdown(
            f'<div class="small muted" style="padding-top:.55rem">'
            f'{"✓ marked as studied" if marked else "not marked yet"}</div>',
            unsafe_allow_html=True)


def _apply_grade(p: dict, qid: str, grade: int) -> None:
    card = p["cards"].get(qid) or srs.new_card()
    p["cards"][qid] = srs.review(card, grade)
    storage.record_answer(p, grade == 2)
    storage.touch()
