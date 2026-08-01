"""Study app for the lecture "Smart Energy Infrastructure"
(KIT, winter term 2025/26 — Pustišek · Ardone · Schuler).

Start:  streamlit run app.py
"""

from __future__ import annotations

from datetime import date

import streamlit as st

st.set_page_config(
    page_title="Smart Energy Infrastructure · Study app",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src import content, storage, theme, ui  # noqa: E402
from src import view_home, view_learn, view_practice, view_recall, view_reference  # noqa: E402

VIEWS = ["Home", "Past exams", "Study", "Practice", "Mock exam",
         "Script", "Glossary", "Statistics", "Settings"]

# Defaults for the greeting - changeable at any time under Settings.
DEFAULT_NAME = "Vincent"
DEFAULT_EXAM = date(2026, 8, 11)
DEFAULT_GOAL = 60


def sidebar(p: dict) -> str:
    with st.sidebar:
        st.markdown(
            """<div class="sb-brand">
            <div class="k">Smart Energy Infrastructure</div>
            <div class="s">Study app · KIT</div></div>""",
            unsafe_allow_html=True)

        current = st.session_state.get("view", "Home")
        st.markdown('<div class="sb-label">Areas</div>', unsafe_allow_html=True)
        for name in VIEWS[:5]:
            if st.button(name, key=f"nav_{name}",
                         type="primary" if name == current else "secondary"):
                _switch(name)
        st.markdown('<div class="sb-label">Look up</div>', unsafe_allow_html=True)
        for name in VIEWS[5:]:
            if st.button(name, key=f"nav_{name}",
                         type="primary" if name == current else "secondary"):
                _switch(name)

        st.markdown('<div class="sb-label">Today</div>', unsafe_allow_html=True)
        goal = int(p.get("goal", DEFAULT_GOAL))
        done = storage.day_entry(p).get("answered", 0)
        streak = storage.streak_value(p)
        left = storage.days_left(p)
        ui.bar(done / max(1, goal), thin=True)
        lines = [f"{done} / {goal} questions",
                 f"{streak} day{'s' if streak != 1 else ''} streak"]
        if left is not None:
            lines.append(f"{max(left, 0)} days until the exam")
        st.markdown(
            '<div class="small muted" style="margin-top:.4rem;line-height:1.7">'
            + "<br>".join(lines) + "</div>",
            unsafe_allow_html=True)

        st.markdown('<div class="sb-label">Appearance</div>', unsafe_allow_html=True)
        dark = p.get("theme") == "dark"
        if st.button("Light mode" if dark else "Dark mode", key="nav_theme"):
            p["theme"] = "light" if dark else "dark"
            storage.touch()
            st.rerun()

        st.markdown(
            '<div class="small" style="margin-top:1.6rem;color:var(--faint);'
            'line-height:1.6">Your progress is saved in this browser '
            'automatically.</div>',
            unsafe_allow_html=True)

    return st.session_state.get("view", "Home")


def _switch(name: str) -> None:
    st.session_state["view"] = name
    if name != "Study":
        st.session_state.pop("learn_unit", None)
    if name != "Practice":
        for key in ("pr_queue", "pr_pos", "pr_run"):
            st.session_state.pop(key, None)
    if name != "Mock exam":
        for key in ("ex_queue", "ex_pos", "ex_res", "ex_started", "ex_saved"):
            st.session_state.pop(key, None)
    if name != "Past exams":
        for key in ("rc_queue", "rc_pos", "rc_run"):
            st.session_state.pop(key, None)
    st.rerun()


def onboarding(p: dict) -> bool:
    """One-off greeting: name, exam date, daily goal."""
    if p.get("name") or st.session_state.get("skip_onboarding"):
        return False

    n_slides = sum(len(u["slides"]) for u in content.build_units())
    n_questions = len(content.load_questions())
    n_recall = len(content.load_pastexams())
    ui.hero("Welcome", "Your study app for Smart Energy Infrastructure",
            f"{n_slides} lecture slides, sorted into chapters and turned into "
            f"{n_questions} questions – {n_recall} of them straight from previous "
            "exams – with explanations, the original slide beside every question and a "
            "system that makes you repeat exactly what has not stuck yet.")

    st.markdown('<div class="card pad-lg">', unsafe_allow_html=True)
    cols = st.columns([1.4, 1.2, 1])
    with cols[0]:
        name = st.text_input("What is your name?", value=DEFAULT_NAME,
                             placeholder="First name")
    with cols[1]:
        exam = st.date_input("When is the exam?", value=DEFAULT_EXAM,
                             format="DD.MM.YYYY")
    with cols[2]:
        goal = st.number_input("Questions per day", 10, 300, DEFAULT_GOAL, step=10)
    st.markdown("</div>", unsafe_allow_html=True)

    ui.spacer("s")
    cols = st.columns([1.4, 1.4, 3])
    with cols[0]:
        if st.button("Let’s go", type="primary", key="ob_go"):
            p["name"] = name.strip() or "you"
            p["exam_date"] = exam.isoformat() if exam else ""
            p["goal"] = int(goal)
            storage.touch()
            st.session_state["view"] = "Past exams"
            st.rerun()
    with cols[1]:
        if st.button("Start without a name", key="ob_skip"):
            st.session_state["skip_onboarding"] = True
            st.rerun()

    ui.spacer()
    st.markdown(
        """<div class="card"><div class="eyebrow">Worth knowing</div>
        <p class="small muted" style="margin-top:.55rem;line-height:1.7">
        Your progress is stored in this browser automatically – you can close the page
        at any time and pick up days later exactly where you left off. No account is
        needed. Under <b>Settings</b> you can also save your state as a file, in case
        you switch device.</p></div>""",
        unsafe_allow_html=True)
    return True


def splash() -> None:
    """A brief moment until the browser has handed over the stored progress."""
    st.markdown(
        """<div class="hero fade" style="margin-top:14vh;text-align:center">
        <div class="eyebrow">Smart Energy Infrastructure</div>
        <h1 style="margin:.5rem 0">Loading your progress …</h1>
        <p class="sub" style="margin:0 auto">One moment – your state is coming out of
        this browser’s storage.</p></div>""",
        unsafe_allow_html=True)
    cols = st.columns([2, 1.6, 2])
    with cols[1]:
        if st.button("Start without saved progress", key="ls_giveup"):
            st.session_state["_ls_give_up"] = True
            st.rerun()


def main() -> None:
    p = storage.boot()
    if p is None:
        theme.inject("light")
        splash()
        return

    theme.inject(p.get("theme", "light"))

    if onboarding(p):
        return

    view = sidebar(p)

    if view == "Home":
        view_home.render(p)
    elif view == "Past exams":
        view_recall.render(p)
    elif view == "Study":
        view_learn.render(p)
    elif view == "Practice":
        view_practice.render_practice(p)
    elif view == "Mock exam":
        view_practice.render_exam(p)
    elif view == "Script":
        view_reference.render_script(p)
    elif view == "Glossary":
        view_reference.render_glossary(p)
    elif view == "Statistics":
        view_reference.render_stats(p)
    else:
        view_reference.render_settings(p)

    # Reward effects at the end of a run
    msg = st.session_state.pop("celebrate", None)
    if msg:
        ui.confetti()
        ui.toast(msg, icon="✨")

    done_unit = st.session_state.pop("learn_done_unit", None)
    if done_unit:
        ui.confetti(intensity=120, seconds=2.6)
        ui.toast(f"Section “{content.unit_label(done_unit)}” finished", icon="✓")

    # Last of all: only runs that get this far send anything to the browser at
    # all. Runs that end in st.rerun() are discarded - the render that follows
    # then stores the current state.
    storage.mirror()


if __name__ == "__main__":
    main()
