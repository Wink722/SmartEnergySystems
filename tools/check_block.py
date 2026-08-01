"""Checks one authoring block before it goes into the catalogue.

    python tools/check_block.py block03

Same rules as tools/check_questions.py, but scoped to a single file so an author
can iterate without waiting for the whole catalogue. Coverage is reported, never
enforced: a slide without a question is fine as long as it is on the block's
exclusion list.
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


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    block = sys.argv[1].removesuffix(".json")

    qfile = DATA / "questions" / f"{block}.json"
    sfile = DATA / "skipped" / f"{block}.json"
    if not qfile.exists():
        print(f"{qfile.relative_to(ROOT)} does not exist")
        return 1

    slides = {s["page"]: s for s in json.loads((DATA / "slides.json").read_text("utf-8"))}
    content = {p for p, s in slides.items() if s["section"]}

    problems: list[str] = []
    try:
        items = json.loads(qfile.read_text("utf-8"))
    except Exception as exc:
        print(f"{qfile.name}: invalid JSON - {exc}")
        return 1
    if not isinstance(items, list):
        print(f"{qfile.name}: file is not an array")
        return 1

    skipped: list[dict] = []
    if sfile.exists():
        try:
            skipped = json.loads(sfile.read_text("utf-8"))
        except Exception as exc:
            problems.append(f"{sfile.name}: invalid JSON - {exc}")

    seen: set[str] = set()
    pages: set[int] = set()
    for q in items:
        qid = q.get("id", "?")
        where = f"{qid}"
        if qid in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(qid)

        page = q.get("slide")
        if page not in slides:
            problems.append(f"{where}: slide {page} does not exist")
        elif page not in content:
            problems.append(f"{where}: slide {page} is not a content slide")
        else:
            pages.add(page)

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
            missing = check_keywords(q.get("solution", ""), kws)["misses"]
            if missing:
                problems.append(f"{where}: keywords absent from its own solution: {missing}")

    # ------------------------------------------------------------- coverage
    block_pages: set[int] = set()
    if pages:
        lo, hi = min(pages), max(pages)
        block_pages = {p for p in content if lo <= p <= hi}
    excluded = {int(s["slide"]) for s in skipped if "slide" in s}
    for s in skipped:
        if "slide" not in s or not str(s.get("reason", "")).strip():
            problems.append(f"skipped: entry without slide or reason: {s}")
        elif int(s["slide"]) in pages:
            problems.append(f"skipped: slide {s['slide']} is on the exclusion list "
                            f"but also has a question")
    unaccounted = sorted(block_pages - pages - excluded)

    types = Counter(q.get("type") for q in items)
    graphic = sum(1 for q in items if q.get("graphic"))
    print(f"{len(items)} questions in {qfile.name}")
    for typ, label in (("open", "open"), ("mc", "multiple choice"), ("cloze", "cloze")):
        share = types[typ] / max(1, len(items)) * 100
        print(f"  {label:16s} {types[typ]:4d}  ({share:4.1f} %)")
    print(f"  with graphic     {graphic:4d}")
    print(f"covered {len(pages)} slides, {len(excluded)} on the exclusion list, "
          f"{len(block_pages)} in the page range")
    if unaccounted:
        print(f"\nneither covered nor excluded ({len(unaccounted)}): {unaccounted}")
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
