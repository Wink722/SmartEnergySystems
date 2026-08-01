"""Practice (spaced repetition) and the mock exam."""

from __future__ import annotations

import html
import random
from datetime import datetime

import streamlit as st

from . import content, qcard, srs, storage, ui


def active_questions(p: dict) -> list[dict]:
    """All questions except the ones deselected as not exam-relevant."""
    skipped = p.get("skipped") or {}
    return [q for q in content.load_questions() if q["id"] not in skipped]


# ============================================================== Practice

def render_practice(p: dict) -> None:
    questions = active_questions(p)
    index = content.question_index()
    chapters = content.chapters()

    if not st.session_state.get("pr_queue"):
        _practice_setup(p, questions, chapters)
        return

    queue: list[str] = st.session_state["pr_queue"]
    pos = int(st.session_state.get("pr_pos", 0))

    if pos >= len(queue):
        _practice_summary(p, early=st.session_state.pop("pr_early", False))
        return

    qid = queue[pos]
    q = index[qid]
    done = pos
    total = len(queue)

    top = st.columns([1.2, 5, 1.4])
    with top[0]:
        if st.button("← Finish", key="pr_quit"):
            st.session_state["pr_early"] = True
            st.session_state["pr_pos"] = len(queue)
            st.rerun()
    with top[2]:
        st.markdown(
            f'<div class="small muted center" style="padding-top:.45rem">{done+1} / {total}</div>',
            unsafe_allow_html=True)

    ui.bar(done / total, thin=True)
    ui.spacer("s")

    card = p["cards"].get(qid)
    st.markdown(
        f'<div style="margin-bottom:.5rem">{qcard.status_badge(card)}</div>',
        unsafe_allow_html=True)

    def _grade(gid: str, grade: int) -> None:
        old_card = p["cards"].get(gid) or srs.new_card()
        p["cards"][gid] = srs.review(old_card, grade)
        storage.record_answer(p, grade == 2)

        run = st.session_state.setdefault("pr_run", {"right": 0, "n": 0, "streak": 0})
        run["n"] += 1
        if grade == 2:
            run["right"] += 1
            run["streak"] += 1
            if run["streak"] in (7, 15, 25, 40):
                st.session_state["celebrate"] = f"{run['streak']} correct in a row!"
        else:
            run["streak"] = 0
            queue.append(gid)          # a miss comes round again at the end
            st.session_state["pr_queue"] = queue

        goal = int(p.get("goal", 60))
        today_n = storage.day_entry(p)["answered"]
        if today_n == goal:
            st.session_state["celebrate"] = f"Daily goal reached: {goal} questions!"

        storage.touch()
        qcard.reset(gid)
        st.session_state["pr_pos"] = pos + 1
        st.rerun()

    qcard.render(q, _grade, position=f"Question {done+1}")


def _practice_setup(p: dict, questions: list[dict], chapters: list[dict]) -> None:
    ui.hero("Practice", "Repetition that adapts",
            "The app pulls the questions that are due right now – answers you got "
            "wrong come back within minutes, ones that sit only much later.")

    all_ids = [q["id"] for q in questions]
    c = srs.counts(all_ids, p["cards"])
    ui.stat_grid([
        (str(c["due"]), "due now", "repetitions"),
        (str(c["new"]), "new", "never seen"),
        (str(c["shaky"]), "shaky", "wrong last time"),
        (str(c["solid"]), "solid", "safely in place"),
    ])
    ui.spacer()

    st.markdown('<div class="eyebrow">What would you like to practise?</div>',
                unsafe_allow_html=True)
    cols = st.columns([2.2, 1.2, 1.2])
    with cols[0]:
        labels = ["All chapters"] + [f"Chapter {c['num']} · {c['title']}" for c in chapters]
        choice = st.selectbox("Scope", labels, label_visibility="collapsed")
    with cols[1]:
        size = st.selectbox("Size", [15, 25, 40, 60], index=1,
                            format_func=lambda n: f"{n} questions",
                            label_visibility="collapsed")
    with cols[2]:
        mode = st.selectbox("Selection", ["mixed", "repetition only", "new questions only",
                                          "shaky only"], label_visibility="collapsed")

    types = st.multiselect(
        "Question types", ["mc", "cloze", "open"],
        default=["mc", "cloze", "open"],
        format_func=lambda t: content.TYPE_LABEL[t])

    pool = questions
    if choice != "All chapters":
        num = int(choice.split()[1].rstrip("·").strip())
        pool = [q for q in pool if q["chapter"] == num]
    if types:
        pool = [q for q in pool if q["type"] in types]
    ids = [q["id"] for q in pool]

    if mode == "repetition only":
        queue = srs.build_queue(ids, p["cards"], limit=size, include_new=False)
    elif mode == "new questions only":
        queue = [i for i in ids if not p["cards"].get(i, {}).get("seen")][:size]
    elif mode == "shaky only":
        queue = [i for i in ids if srs.status(p["cards"].get(i)) == "shaky"][:size]
    else:
        queue = srs.build_queue(ids, p["cards"], limit=size)

    ui.spacer("s")
    st.markdown(
        f'<div class="small muted">{len(queue)} questions ready '
        f'(out of {len(ids)} in the chosen scope).</div>', unsafe_allow_html=True)
    ui.spacer("s")

    start = st.columns([1.3, 1, 3])
    with start[0]:
        if st.button("Start the round", type="primary", key="pr_start", disabled=not queue):
            st.session_state["pr_queue"] = queue
            st.session_state["pr_pos"] = 0
            st.session_state["pr_run"] = {"right": 0, "n": 0, "streak": 0}
            st.rerun()
    with start[1]:
        if st.button("Random round", key="pr_rand", disabled=not ids):
            rnd = random.sample(ids, min(size, len(ids)))
            st.session_state["pr_queue"] = rnd
            st.session_state["pr_pos"] = 0
            st.session_state["pr_run"] = {"right": 0, "n": 0, "streak": 0}
            st.rerun()

    if not queue:
        ui.spacer()
        st.markdown(
            """<div class="card"><div class="eyebrow">Nothing due</div>
            <p class="small muted" style="margin-top:.5rem">Nothing is up for repetition
            in this selection – which is a good sign. Switch to “new questions only”,
            start a random round, or go back to Study.</p></div>""",
            unsafe_allow_html=True)


def _practice_summary(p: dict, early: bool = False) -> None:
    run = st.session_state.get("pr_run", {"right": 0, "n": 0})
    n, right = run.get("n", 0), run.get("right", 0)
    rate = int(round(right / n * 100)) if n else 0

    ui.hero("Round over", "Finished" if not early else "Round stopped")
    ui.stat_grid([
        (str(n), "answered", ""),
        (f"{rate} %", "hit rate", f"{right} correct"),
        (str(storage.day_entry(p)["answered"]), "today in total",
         f"goal: {p.get('goal', 60)}"),
    ])
    ui.spacer()

    if n and rate >= 80:
        st.markdown(
            """<div class="acard fade"><div class="lab">Strong</div>
            <p>Over 80 % correct – those cards move into longer intervals and will not
            be back for a while.</p></div>""", unsafe_allow_html=True)
    elif n:
        st.markdown(
            """<div class="acard miss fade"><div class="lab">Keep at it</div>
            <p>The questions you got wrong have dropped back to box 0 – they will return
            in a few minutes. That is exactly how it should work.</p></div>""",
            unsafe_allow_html=True)

    ui.spacer()
    cols = st.columns([1.2, 1.2, 3])
    with cols[0]:
        if st.button("Another round", type="primary", key="pr_again"):
            for k in ("pr_queue", "pr_pos", "pr_run"):
                st.session_state.pop(k, None)
            st.rerun()
    with cols[1]:
        if st.button("Back home", key="pr_home"):
            for k in ("pr_queue", "pr_pos", "pr_run"):
                st.session_state.pop(k, None)
            st.session_state["view"] = "Home"
            st.rerun()


# ============================================================== Mock exam

def render_exam(p: dict) -> None:
    index = content.question_index()

    if not st.session_state.get("ex_queue"):
        _exam_setup(p)
        return

    queue: list[str] = st.session_state["ex_queue"]
    pos = int(st.session_state.get("ex_pos", 0))

    if pos >= len(queue):
        _exam_result(p)
        return

    started = st.session_state.get("ex_started")
    limit = int(st.session_state.get("ex_minutes", 90))
    elapsed = (datetime.now() - started).total_seconds() / 60 if started else 0
    left = max(0.0, limit - elapsed)

    top = st.columns([1.2, 4, 1.6])
    with top[0]:
        if st.button("Hand in", key="ex_submit"):
            st.session_state["ex_pos"] = len(queue)
            st.rerun()
    with top[2]:
        tone = "bad" if left < 5 else ("warn" if left < 12 else "ok")
        st.markdown(
            f'<div style="text-align:right;padding-top:.35rem">'
            f'{ui.chip(f"{int(left)} min left", tone)}</div>', unsafe_allow_html=True)

    ui.bar(pos / len(queue), thin=True)
    ui.spacer("s")

    if left <= 0:
        st.warning("Time is up – the exam is being marked.")
        st.session_state["ex_pos"] = len(queue)
        st.rerun()

    qid = queue[pos]
    q = index[qid]

    def _grade(gid: str, grade: int) -> None:
        st.session_state.setdefault("ex_res", {})[gid] = grade
        card = p["cards"].get(gid) or srs.new_card()
        p["cards"][gid] = srs.review(card, grade)
        storage.record_answer(p, grade == 2)
        storage.touch()
        qcard.reset(gid)
        st.session_state["ex_pos"] = pos + 1
        st.rerun()

    qcard.render(q, _grade, position=f"Task {pos+1} of {len(queue)}",
                 exam_mode=True, show_source=False)


def _exam_setup(p: dict) -> None:
    chapters = content.chapters()
    questions = active_questions(p)

    ui.hero("Mock exam", "Under time pressure",
            "A drawn set of tasks against the clock – with model answers to compare "
            "against and a breakdown by chapter at the end.")

    cols = st.columns([2, 1.1, 1.1])
    with cols[0]:
        labels = ["All chapters"] + [f"Chapter {c['num']} · {c['title']}" for c in chapters]
        choice = st.selectbox("Scope", labels, label_visibility="collapsed")
    with cols[1]:
        count = st.selectbox("Tasks", [10, 15, 20, 30], index=1,
                             format_func=lambda n: f"{n} tasks",
                             label_visibility="collapsed")
    with cols[2]:
        # 90 minutes as the default - that is how long the real exam runs.
        minutes = st.selectbox("Time", [20, 30, 45, 60, 90], index=4,
                               format_func=lambda n: f"{n} minutes",
                               label_visibility="collapsed")

    focus = st.radio("Emphasis",
                     ["exam-like (open questions, many real past-exam questions)",
                      "mixed", "multiple choice only"],
                     horizontal=True, label_visibility="collapsed")

    pool = questions
    if choice != "All chapters":
        num = int(choice.split()[1].rstrip("·").strip())
        pool = [q for q in pool if q["chapter"] == num]

    if focus.startswith("exam-like"):
        # Half of the open tasks come from the memory protocols - you cannot get
        # closer to the real exam than that.
        recall = [q["id"] for q in pool if q.get("recall")]
        opens = [q["id"] for q in pool if q["type"] == "open" and not q.get("recall")]
        others = [q["id"] for q in pool if q["type"] != "open"]
        n_open = int(count * 0.7)
        sel = random.sample(recall, min(len(recall), max(1, n_open // 2)))
        sel += random.sample(opens, min(max(0, n_open - len(sel)), len(opens)))
        sel += random.sample(others, min(max(0, count - len(sel)), len(others)))
    elif focus == "multiple choice only":
        mcs = [q["id"] for q in pool if q["type"] == "mc"]
        sel = random.sample(mcs, min(count, len(mcs)))
    else:
        ids = [q["id"] for q in pool]
        sel = random.sample(ids, min(count, len(ids)))
    random.shuffle(sel)

    ui.spacer("s")
    st.markdown(f'<div class="small muted">{len(sel)} tasks, {minutes} minutes.</div>',
                unsafe_allow_html=True)
    ui.spacer("s")

    if st.button("Start the exam", type="primary", key="ex_start", disabled=not sel):
        st.session_state["ex_queue"] = sel
        st.session_state["ex_pos"] = 0
        st.session_state["ex_res"] = {}
        st.session_state["ex_minutes"] = minutes
        st.session_state["ex_started"] = datetime.now()
        st.rerun()

    if p.get("exams"):
        ui.spacer()
        ui.section_title("Earlier mock exams")
        rows = ""
        for e in reversed(p["exams"][-8:]):
            rows += (f'<div class="rowline"><span class="nm">{html.escape(e["date"][:16])}'
                     f'<span class="small muted"> · {e["n"]} tasks</span></span>'
                     f'<b>{e["score"]} %</b></div>')
        st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)


def _exam_result(p: dict) -> None:
    res: dict[str, int] = st.session_state.get("ex_res", {})
    index = content.question_index()
    n = len(res)
    points = sum(res.values())
    score = int(round(points / (2 * n) * 100)) if n else 0

    if not st.session_state.get("ex_saved"):
        p["exams"].append({"date": datetime.now().replace(microsecond=0).isoformat(),
                           "n": n, "score": score})
        storage.touch()
        st.session_state["ex_saved"] = True
        if score >= 75:
            st.session_state["celebrate"] = f"Mock exam passed – {score} %!"

    ui.hero("Result", f"{score} % reached",
            "Marking follows your own assessment: “Solid” = 2 points, “Half” = 1 point, "
            "“Off” = 0.")

    full = sum(1 for g in res.values() if g == 2)
    half = sum(1 for g in res.values() if g == 1)
    ui.stat_grid([
        (f"{points}", "points", f"of {2*n} possible"),
        (str(full), "knew it safely", ""),
        (str(half), "half knew it", ""),
        (str(n - full - half), "did not know it", ""),
    ])
    ui.spacer()

    by_ch: dict[int, list[int]] = {}
    for qid, grade in res.items():
        by_ch.setdefault(index[qid]["chapter"], []).append(grade)
    rows = ""
    for ch in sorted(by_ch):
        grades = by_ch[ch]
        pct = int(round(sum(grades) / (2 * len(grades)) * 100))
        tone = "ok" if pct >= 75 else ("warn" if pct >= 50 else "bad")
        rows += (f'<div class="rowline"><span class="nm"><b>Chapter {ch}</b>'
                 f'<span class="small muted"> · {len(grades)} tasks</span></span>'
                 f'{ui.chip(f"{pct} %", tone)}</div>')
    st.markdown(f'<div class="card"><div class="eyebrow">By chapter</div>{rows}</div>',
                unsafe_allow_html=True)

    weak = [qid for qid, g in res.items() if g < 2]
    if weak:
        ui.spacer()
        with st.expander(f"Read up on the {len(weak)} tasks that did not sit"):
            for qid in weak:
                q = index[qid]
                st.markdown(
                    f"""<div style="padding:.7rem 0;border-bottom:1px solid var(--line)">
                    <div class="small" style="font-weight:600">{html.escape(q['prompt'])}</div>
                    <div class="small muted" style="margin-top:.35rem;line-height:1.6">
                    {html.escape(q['solution'])}</div>
                    <div class="small" style="margin-top:.3rem;color:var(--accent)">
                    Slide {q['slide']}</div></div>""",
                    unsafe_allow_html=True)

    ui.spacer()
    cols = st.columns([1.3, 1.3, 3])
    with cols[0]:
        if st.button("Another exam", type="primary", key="ex_again"):
            for k in ("ex_queue", "ex_pos", "ex_res", "ex_started", "ex_saved"):
                st.session_state.pop(k, None)
            st.rerun()
    with cols[1]:
        if st.button("Back home", key="ex_home"):
            for k in ("ex_queue", "ex_pos", "ex_res", "ex_started", "ex_saved"):
                st.session_state.pop(k, None)
            st.session_state["view"] = "Home"
            st.rerun()
