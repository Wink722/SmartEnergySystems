"""Loading and indexing of the study content (slides, questions, learning path)."""

from __future__ import annotations

import glob
import json
import re
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PDF_PATH = ROOT / "smart_energy_systems.pdf"

TYPE_LABEL = {"mc": "Multiple choice", "cloze": "Fill in the term",
              "open": "Open question"}


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def load_slides() -> dict[int, dict]:
    return {s["page"]: s for s in _read(DATA / "slides.json")}


@st.cache_data(show_spinner=False)
def load_guide() -> dict:
    return _read(DATA / "guide.json")


@st.cache_data(show_spinner=False)
def load_pastexams() -> list[dict]:
    """Questions from the memory protocols - the ones that really came up.

    They join the same pool as the rest of the catalogue as open questions, so
    they appear while studying, while practising and in the mock exam. `recall`
    marks them everywhere.
    """
    out: list[dict] = []
    for file in sorted(glob.glob(str(DATA / "pastexams" / "*.json"))):
        for a in _read(Path(file)):
            q = dict(a)
            q["type"] = "open"
            q["recall"] = True
            q["slides"] = list(a.get("slides") or [])
            q["slide"] = q["slides"][0] if q["slides"] else 0
            out.append(q)
    out.sort(key=lambda q: q["nr"])
    return out


@st.cache_data(show_spinner=False)
def recall_slides() -> dict[int, list[str]]:
    """Slide -> ids of the past-exam questions that rest on it."""
    out: dict[int, list[str]] = {}
    for q in load_pastexams():
        for page in q["slides"]:
            out.setdefault(page, []).append(q["id"])
    return out


@st.cache_data(show_spinner=False)
def load_questions() -> list[dict]:
    """All questions, enriched with chapter and section from the slide data."""
    slides = load_slides()
    out: list[dict] = []
    files = sorted(glob.glob(str(DATA / "questions" / "*.json")))
    for file in files:
        for q in _read(Path(file)):
            s = slides.get(q["slide"], {})
            q["chapter"] = s.get("chapter", 0)
            q["chapter_title"] = s.get("chapter_title", "")
            q["block"] = s.get("block", "")
            q["part"] = s.get("part", "")
            q["section"] = s.get("section", "")
            q["slide_title"] = s.get("title", "")
            q["slide_graphic"] = s.get("graphic", False)
            q["unit"] = unit_key(q["chapter"], q["part"], q["section"])
            out.append(q)

    for q in load_pastexams():
        s = slides.get(q["slide"], {})
        q = dict(q)
        q["chapter"] = s.get("chapter", q.get("chapter", 0))
        q["chapter_title"] = s.get("chapter_title", "")
        q["block"] = s.get("block", "")
        q["part"] = s.get("part", "")
        q["section"] = s.get("section", "")
        q["slide_title"] = s.get("title", "")
        q["slide_graphic"] = s.get("graphic", False)
        q["unit"] = unit_key(q["chapter"], q["part"], q["section"])
        out.append(q)

    out.sort(key=lambda q: (q["chapter"], q["slide"], q["id"]))
    return out


def unit_key(chapter: int, part: str, section: str) -> str:
    """One study unit = a section (level 2), otherwise the part (level 1)."""
    return f"{chapter}|{section or part}"


def unit_label(key: str) -> str:
    return key.split("|", 1)[1] if "|" in key else key


@st.cache_data(show_spinner=False)
def build_units() -> list[dict]:
    """Learning path: ordered list of all study units with slides and questions."""
    slides = load_slides()
    guide = load_guide()
    questions = load_questions()

    intros: dict[str, str] = {}
    for u in guide["units"]:
        key = unit_key(u["chapter"], u.get("part", ""), u.get("section", ""))
        intros[key] = u["intro"]

    by_unit: dict[str, dict] = {}
    order: list[str] = []
    for page in sorted(slides):
        s = slides[page]
        if s["chapter"] == 0 or not (s["part"] or s["section"]):
            continue
        key = unit_key(s["chapter"], s["part"], s["section"])
        if key not in by_unit:
            by_unit[key] = {
                "key": key,
                "chapter": s["chapter"],
                "chapter_title": s["chapter_title"],
                "block": s["block"],
                "part": s["part"],
                "label": s["section"] or s["part"],
                "intro": intros.get(key, ""),
                "slides": [],
                "questions": [],
            }
            order.append(key)
        by_unit[key]["slides"].append(page)

    for q in questions:
        if q["unit"] in by_unit:
            by_unit[q["unit"]]["questions"].append(q["id"])

    return [by_unit[k] for k in order if by_unit[k]["questions"]]


@st.cache_data(show_spinner=False)
def question_index() -> dict[str, dict]:
    return {q["id"]: q for q in load_questions()}


@st.cache_data(show_spinner=False)
def questions_by_slide() -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    for q in load_questions():
        out.setdefault(q["slide"], []).append(q["id"])
    return out


@st.cache_data(show_spinner=False)
def chapters() -> list[dict]:
    guide = load_guide()["chapters"]
    units = build_units()
    out = []
    for num in sorted({u["chapter"] for u in units}):
        meta = guide.get(str(num), {})
        us = [u for u in units if u["chapter"] == num]
        out.append({
            "num": num,
            "title": meta.get("title", f"Chapter {num}"),
            "block": us[0]["block"] if us else "",
            "intro": meta.get("intro", ""),
            "thread": meta.get("thread", ""),
            "units": us,
            "n_slides": sum(len(u["slides"]) for u in us),
            "n_questions": sum(len(u["questions"]) for u in us),
        })
    return out


@st.cache_data(show_spinner=False)
def blocks() -> list[dict]:
    """The three lecture blocks with their chapters - used for grouping."""
    out: list[dict] = []
    for ch in chapters():
        if not out or out[-1]["name"] != ch["block"]:
            out.append({"name": ch["block"], "chapters": []})
        out[-1]["chapters"].append(ch)
    return out


# ---------------------------------------------------------------- glossary

@st.cache_data(show_spinner=False)
def glossary() -> list[dict]:
    """Terms from the cloze questions, each with a definition and a slide."""
    entries: dict[str, dict] = {}
    for q in load_questions():
        if q["type"] != "cloze":
            continue
        term = (q.get("accept") or [""])[0].strip()
        # A gap can also ask for a quantity ("90 days", "42 %"). Those are good
        # questions but bad glossary entries - an entry has to be a term, so it
        # must start with a letter and carry enough letters to be one.
        if not term[:1].isalpha():
            continue
        if len(re.sub(r"[^A-Za-zÄÖÜäöüß]", "", term)) < 4:
            continue
        if term.lower() in entries:
            continue
        entries[term.lower()] = {
            "term": term,
            "definition": q["solution"],
            "slide": q["slide"],
            "chapter": q["chapter"],
            "section": q["section"] or q["part"],
            "qid": q["id"],
        }
    return sorted(entries.values(), key=lambda e: e["term"].lower())


@st.cache_data(show_spinner=False)
def search(term: str, limit: int = 40) -> dict[str, list]:
    """Full-text search across questions, model answers and slide text."""
    t = term.strip().lower()
    if len(t) < 2:
        return {"questions": [], "slides": []}

    qhits = []
    for q in load_questions():
        blob = " ".join([q["prompt"], q.get("solution", ""),
                         " ".join(q.get("keywords", []))]).lower()
        if t in blob:
            qhits.append(q)
        if len(qhits) >= limit:
            break

    shits = []
    for page, s in load_slides().items():
        if s["chapter"] == 0:
            continue
        if t in (s["title"] + " " + s["text"]).lower():
            shits.append(s)
        if len(shits) >= limit:
            break

    return {"questions": qhits, "slides": shits}
