"""Relevance score per question + selection for the exam-practice booklet."""
import json, glob, os, re
from collections import Counter, defaultdict

R = r"C:\Users\vince\Desktop\Studium\smart Energy Systems\SmartEnergySystems"

SLIDES = {s["page"]: s for s in json.load(open(os.path.join(R, "data", "slides.json"), encoding="utf-8"))}

# Sections the memory protocols keep coming back to.
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


def load():
    qs = []
    for f in sorted(glob.glob(os.path.join(R, "data", "questions", "*.json"))):
        for q in json.load(open(f, encoding="utf-8")):
            q["recall"] = False
            qs.append(q)
    past = []
    for f in sorted(glob.glob(os.path.join(R, "data", "pastexams", "*.json"))):
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
    body = q.get("solution", "") + " " + q.get("prompt", "")
    if q.get("graphic") or CALC.search(body):
        v += 1
    return max(2, min(5, v))


def main():
    qs, past = load()
    recall_slides = set()
    for a in past:
        recall_slides |= set(a.get("slides") or [])
    for q in qs:
        q["score"] = score(q, recall_slides)
    for a in past:
        a["score"] = 5

    print("Score-Verteilung im Katalog:", dict(sorted(Counter(q["score"] for q in qs).items())))

    # Selection. All past-exam questions are set. The rest is allocated per
    # chapter proportionally to how much material the chapter has, with a
    # surcharge for chapters a protocol has already touched - exam-weighted,
    # but nothing left uncovered.
    TARGET = 100
    chosen = list(past)
    by_ch = defaultdict(list)
    for q in qs:
        by_ch[q["chapter"]].append(q)
    for ch in by_ch:
        by_ch[ch].sort(key=lambda q: (-q["score"], q["slide"]))

    slides_per_ch = Counter(s["chapter"] for s in SLIDES.values() if s["section"])
    past_per_ch = Counter(a["chapter"] for a in past)
    fill = TARGET - len(past)
    weight = {ch: slides_per_ch[ch] * (1.5 if past_per_ch.get(ch) else 1.0)
              for ch in by_ch}
    total_w = sum(weight.values())
    quota = {}
    for ch in by_ch:
        quota[ch] = max(3, min(11, round(fill * weight[ch] / total_w)))
    # renormalise to the budget
    while sum(quota.values()) > fill:
        ch = max(quota, key=lambda c: (quota[c], weight[c]))
        if quota[ch] <= 3:
            break
        quota[ch] -= 1
    while sum(quota.values()) < fill:
        ch = min(quota, key=lambda c: (quota[c] / max(1, weight[c])))
        quota[ch] += 1

    for ch in sorted(by_ch):
        chosen += by_ch[ch][:quota[ch]]
    print("Quote je Kapitel:", dict(sorted(quota.items())))

    chosen.sort(key=lambda q: (q["chapter"], not q["recall"], -q["score"], q["slide"]))
    print(f"ausgewaehlt: {len(chosen)} Fragen "
          f"({sum(1 for q in chosen if q['recall'])} Altklausur)")
    print("je Kapitel:", dict(sorted(Counter(q["chapter"] for q in chosen).items())))
    print("Typen:", dict(Counter(q["type"] for q in chosen)))
    # A figure only goes in where the question cannot be answered without it.
    NEEDS_FIG = re.compile(
        r"\bdraw\b|\blabel\b|\bsketch\b|the figure|the chart|the table|the diagram|"
        r"read off|reproduce|the slide shows|the slide plots|on the axes", re.I)
    for q in chosen:
        q["figure"] = bool(q.get("graphic")) and bool(NEEDS_FIG.search(q["prompt"]))
    figs = [q for q in chosen if q["figure"]]
    figs.sort(key=lambda q: (-q["score"], q["chapter"]))
    keep = {q["id"] for q in figs[:15]}
    for q in chosen:
        q["figure"] = q["id"] in keep
    print("Abbildungen:", sum(1 for q in chosen if q["figure"]))
    json.dump(chosen, open(os.path.join(os.path.dirname(__file__), "selection.json"), "w",
                           encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
