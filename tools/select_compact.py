"""Selection for the compact, black-and-white exam drill.

Unlike tools/score_questions.py, which builds a pure priority list, this one
guarantees that **every one of the 80 sections is represented**. The first pass
found that a top-scored-per-chapter selection clusters: chapter 4 got 16
questions, almost all of them on the storage-cost slides, while 49 sections had
nothing at all - including several the past exams had touched.

Order of allocation:
  1. every past-exam question
  2. one question for each section that is still empty
  3. fill up by relevance score

    python tools/select_compact.py
"""

from __future__ import annotations

import glob
import json
import os
import re
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "selection_compact.json")
TARGET = 160

SLIDES = {s["page"]: s for s in
          json.load(open(os.path.join(ROOT, "data", "slides.json"), encoding="utf-8"))}

HIGH_YIELD = {
    "Transport prices and pricing systems", "Storage basics, parameters and functions",
    "Storage contracts and pricing", "Security of supply", "Gas prices, hubs and swaps",
    "Natural monopoly and unbundling", "Regulation: goals, authorities and forms",
    "Infrastructure: definition and types", "LNG value chain",
    "Pipeline economics: diameter and compression", "Marginal costs and merit order",
    "Exercise: cost-minimal load coverage", "Availability and the convolution method",
    "Peak-load pricing on a green field", "Expansion planning exercise",
    "Perfect foresight vs. time-step", "Combining scenario planning and energy systems analysis",
    "Decision rules under uncertainty", "Net present value method", "Annuity method",
    "System services and control reserve", "Electrical fundamentals and transmission losses",
    "Electrolysis and hydrogen production", "Ammonia", "Comparison of hydrogen derivatives",
    "Modes of oil transport", "Gas quality parameters",
    "Challenges, industry example and exercise", "Methanol and carbon capture",
}

CALC = re.compile(r"\d\s*[·*×/+]\s*\d|=\s*[\d(]|€/|kWh|MWh|%/|Nm³|kg/")
NEEDS_FIG = re.compile(
    r"\bdraw\b|\blabel\b|\bsketch\b|the figure|the chart|the table|the diagram|"
    r"read off|reproduce|the slide shows|the slide plots|on the axes", re.I)


def load():
    qs, past = [], []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "questions", "*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            q["recall"] = False
            qs.append(q)
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "pastexams", "*.json"))):
        for a in json.load(open(f, encoding="utf-8")):
            a = dict(a)
            a["recall"] = True
            a["type"] = "open"
            a["slide"] = (a.get("slides") or [0])[0]
            past.append(a)
    for q in qs + past:
        s = SLIDES.get(q["slide"], {})
        q["chapter"] = s.get("chapter", q.get("chapter", 0))
        q["chapter_title"] = s.get("chapter_title", "")
        q["section"] = s.get("section", "")
        q["block"] = s.get("block", "")
        q["slide_title"] = s.get("title", "")
    return qs, past


def score(q, recall_slides):
    if q["recall"]:
        return 5
    v = 3
    if q["slide"] in recall_slides:
        v += 1
    if q.get("section") in HIGH_YIELD:
        v += 1
    if q.get("graphic") or CALC.search(q.get("solution", "") + " " + q.get("prompt", "")):
        v += 1
    return max(2, min(5, v))


def main() -> None:
    qs, past = load()
    recall_slides = set()
    for a in past:
        recall_slides |= set(a.get("slides") or [])
    for q in qs:
        q["score"] = score(q, recall_slides)
    for a in past:
        a["score"] = 5

    chosen = list(past)
    have = {q["id"] for q in chosen}
    covered = {(q["chapter"], q["section"]) for q in chosen if q.get("section")}

    by_sec = defaultdict(list)
    for q in qs:
        if q.get("section"):
            by_sec[(q["chapter"], q["section"])].append(q)
    for key in by_sec:
        by_sec[key].sort(key=lambda q: (-q["score"], q["slide"]))

    # 2 - one question for every section that is still empty
    for key in sorted(by_sec):
        if key not in covered:
            chosen.append(by_sec[key][0])
            have.add(by_sec[key][0]["id"])
            covered.add(key)

    # 3 - fill by score, but spread: round-robin over the sections
    pools = {k: [q for q in v if q["id"] not in have] for k, v in by_sec.items()}
    while len(chosen) < TARGET:
        best = None
        for key, pool in pools.items():
            if not pool:
                continue
            cand = pool[0]
            rank = (-cand["score"], sum(1 for c in chosen if c.get("section") == key[1]))
            if best is None or rank < best[0]:
                best = (rank, key)
        if best is None:
            break
        chosen.append(pools[best[1]].pop(0))

    chosen.sort(key=lambda q: (q["chapter"], not q["recall"], -q["score"], q["slide"]))

    figs = [q for q in chosen if q.get("graphic") and NEEDS_FIG.search(q["prompt"])]
    figs.sort(key=lambda q: (-q["score"], q["chapter"]))
    keep = {q["id"] for q in figs[:18]}
    for q in chosen:
        q["figure"] = q["id"] in keep

    all_sec = {(s["chapter"], s["section"]) for s in SLIDES.values() if s["section"]}
    got_sec = {(q["chapter"], q["section"]) for q in chosen if q.get("section")}
    print(f"{len(chosen)} Fragen ({sum(1 for q in chosen if q['recall'])} Altklausur)")
    print(f"Abschnitte: {len(got_sec)} von {len(all_sec)}  |  "
          f"Folien: {len({q['slide'] for q in chosen})}")
    print("je Kapitel:", dict(sorted(Counter(q["chapter"] for q in chosen).items())))
    print("Typen:", dict(Counter(q["type"] for q in chosen)))
    print("Abbildungen:", sum(1 for q in chosen if q["figure"]))
    missing = sorted(all_sec - got_sec)
    if missing:
        print("OHNE FRAGE:", missing)
    json.dump(chosen, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
