"""Checks the question catalogue for completeness and consistency.

    python tools/check_questions.py
    python tools/check_questions.py --excluded    # with the reason for each skip

Checked:
  * valid JSON, unique ids, known question types
  * slide references point at real content slides
  * mc: four options, correct index in range
  * cloze: at least one accepted spelling, gap present
  * open: every keyword also appears in its own model answer
  * coverage: a slide without a question is fine **as long as it is on the
    exclusion list** in data/skipped/ together with a reason. Unlike the sister
    app, this catalogue deliberately leaves non-examinable slides out; the run
    lists them, but only slides that are neither covered nor excluded count as
    a problem.
  * learning path: every unit has an intro, every chapter an entry
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.grading import check_keywords  # noqa: E402

DATA = ROOT / "data"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    slides = {s["page"]: s for s in load_json(DATA / "slides.json")}
    content_pages = {p for p, s in slides.items() if s["section"]}
    guide = load_json(DATA / "guide.json")

    problems: list[str] = []
    questions: list[dict] = []
    seen_ids: set[str] = set()

    files = sorted((DATA / "questions").glob("*.json"))
    if not files:
        print("No question files found.")
        return 1

    for file in files:
        try:
            items = load_json(file)
        except Exception as exc:
            problems.append(f"{file.name}: invalid JSON - {exc}")
            continue
        if not isinstance(items, list):
            problems.append(f"{file.name}: file is not an array")
            continue
        for q in items:
            if not isinstance(q, dict):
                problems.append(f"{file.name}: entry is not an object: {str(q)[:60]!r}")
                continue
            qid = q.get("id", "?")
            where = f"{file.name} · {qid}"
            if qid in seen_ids:
                problems.append(f"{where}: duplicate id")
            seen_ids.add(qid)

            page = q.get("slide")
            if page not in slides:
                problems.append(f"{where}: slide {page} does not exist")
            elif page not in content_pages:
                problems.append(f"{where}: slide {page} is not a content slide")

            typ = q.get("type")
            if typ not in ("open", "mc", "cloze"):
                problems.append(f"{where}: unknown type {typ!r}")
            if not q.get("prompt"):
                problems.append(f"{where}: no prompt")
            if not q.get("solution"):
                problems.append(f"{where}: no model answer")

            if typ == "mc":
                options = q.get("options") or []
                correct = q.get("correct") or []
                if len(options) != 4:
                    problems.append(f"{where}: {len(options)} options instead of 4")
                if not correct:
                    problems.append(f"{where}: no correct option marked")
                for idx in correct:
                    if not isinstance(idx, int) or not 0 <= idx < len(options):
                        problems.append(f"{where}: correct index {idx} out of range")
            elif typ == "cloze":
                if not q.get("accept"):
                    problems.append(f"{where}: no accepted answer")
                if "___" not in (q.get("prompt") or ""):
                    problems.append(f"{where}: gap '___' missing from the prompt")
            elif typ == "open":
                kws = q.get("keywords") or []
                if len(kws) < 3:
                    problems.append(f"{where}: only {len(kws)} keywords")
                # The model answer has to contain its own keywords, otherwise the
                # keyword check marks terms as missed that were never there.
                missing = check_keywords(q.get("solution", ""), kws)["misses"]
                if missing:
                    problems.append(f"{where}: keywords absent from the answer: {missing}")

            questions.append(q)

    # -------------------------------------------------- past-exam questions
    past_files = sorted((DATA / "pastexams").glob("*.json"))
    past: list[dict] = []
    for file in past_files:
        try:
            items = load_json(file)
        except Exception as exc:
            problems.append(f"{file.name}: invalid JSON - {exc}")
            continue
        for a in items:
            if not isinstance(a, dict):
                problems.append(f"{file.name}: entry is not an object: {str(a)[:60]!r}")
                continue
            where = f"{file.name} · {a.get('id', '?')}"
            if a.get("id") in seen_ids:
                problems.append(f"{where}: duplicate id")
            seen_ids.add(a.get("id"))
            if not a.get("solution"):
                problems.append(f"{where}: no model answer")
            for page in a.get("slides") or []:
                if page not in slides:
                    problems.append(f"{where}: slide {page} does not exist")
            if not (a.get("slides") or []):
                problems.append(f"{where}: no slide reference")
            missing = check_keywords(a.get("solution", ""), a.get("keywords") or [])["misses"]
            if missing:
                problems.append(f"{where}: keywords absent from the answer: {missing}")
            past.append(a)

    if past:
        nums = sorted(a.get("nr", 0) for a in past)
        gaps_nr = [n for n in range(1, max(nums) + 1) if n not in nums]
        print(f"{len(past)} past-exam questions from {len(past_files)} files, "
              f"{sum(1 for a in past if a.get('hot'))} marked as very frequent, "
              f"{sum(int(a.get('count', 1)) for a in past)} appearances")
        if gaps_nr:
            problems.append(f"pastexams: missing numbers {gaps_nr}")

    # ------------------------------------------------------- exclusion list
    excluded: dict[int, str] = {}
    for file in sorted((DATA / "skipped").glob("*.json")):
        try:
            items = load_json(file)
        except Exception as exc:
            problems.append(f"{file.name}: invalid JSON - {exc}")
            continue
        for entry in items:
            if not isinstance(entry, dict):
                problems.append(f"{file.name}: entry is not an object: {str(entry)[:60]!r}")
                continue
            page = entry.get("slide")
            reason = str(entry.get("reason", "")).strip()
            if page not in slides:
                problems.append(f"{file.name}: slide {page} does not exist")
                continue
            if not reason:
                problems.append(f"{file.name}: slide {page} excluded without a reason")
            excluded[page] = reason

    covered = {q["slide"] for q in questions}
    for page in sorted(covered & set(excluded)):
        problems.append(f"slide {page} is on the exclusion list and has a question")

    uncovered = sorted(content_pages - covered)
    unaccounted = [p for p in uncovered if p not in excluded]

    types = Counter(q.get("type") for q in questions)
    graphic = sum(1 for q in questions if q.get("graphic"))

    print(f"{len(questions)} questions from {len(files)} files")
    for typ, label in (("open", "open questions"), ("mc", "multiple choice"),
                       ("cloze", "fill in the term")):
        share = types[typ] / max(1, len(questions)) * 100
        print(f"  {label:22s} {types[typ]:4d}  ({share:4.1f} %)")
    print(f"  of those graphic       {graphic:4d}")
    print(f"Coverage: {len(covered & content_pages)} of {len(content_pages)} content "
          f"slides carry a question, {len(excluded)} are deliberately excluded")

    by_chapter = Counter(slides[q["slide"]]["chapter"] for q in questions
                         if q["slide"] in slides)
    for ch in sorted(by_chapter):
        pages = [p for p in content_pages if slides[p]["chapter"] == ch]
        miss = [p for p in pages if p not in covered and p not in excluded]
        skip = [p for p in pages if p in excluded]
        print(f"  Chapter {ch:>2}: {by_chapter[ch]:4d} questions, {len(pages)} slides, "
              f"{len(skip)} excluded"
              f"{'' if not miss else f', UNACCOUNTED: {miss}'}")

    # -------------------------------------------------------- learning path
    intros = {(u["chapter"], u.get("section", "")) for u in guide["units"]}
    units = {(s["chapter"], s["section"]) for s in slides.values() if s["section"]}
    for ch, sec in sorted(units - intros):
        problems.append(f"guide.json: no intro for chapter {ch} · {sec}")
    for ch in sorted({s["chapter"] for s in slides.values() if s["section"]}):
        if str(ch) not in guide["chapters"]:
            problems.append(f"guide.json: no chapter entry for chapter {ch}")

    if excluded:
        if "--excluded" in sys.argv:
            print(f"\nDeliberately left without a question ({len(excluded)}):")
            for page in sorted(excluded):
                s = slides[page]
                print(f"  {page:>4}  ch{s['chapter']:<3}{s['title'][:52]:54s}{excluded[page]}")
        else:
            print(f"\nDeliberately left without a question ({len(excluded)}): "
                  f"{sorted(excluded)}"
                  f"\n     (run with --excluded to see the reasons)")
    if unaccounted:
        print(f"\nNeither covered nor excluded ({len(unaccounted)}): {unaccounted}")
        problems.append(f"{len(unaccounted)} slides are neither covered nor on the "
                        f"exclusion list")

    if problems:
        print(f"\n{len(problems)} problems:")
        for line in problems:
            print("  -", line)
        return 1
    print("\nAll good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
