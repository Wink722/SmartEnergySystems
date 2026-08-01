"""Shuffles the answer options of the multiple-choice questions.

The app shows the options in file order. If the correct answers are mostly
written first, the solution can be read off the position instead of the content.
This script shuffles every question deterministically (seed = question id) and
carries the `correct` indices along, so it can be applied safely.

    python tools/shuffle_mc.py
"""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "questions"


def main() -> None:
    before: Counter = Counter()
    after: Counter = Counter()
    touched = 0

    for file in sorted(DATA.glob("*.json")):
        items = json.loads(file.read_text(encoding="utf-8"))
        changed = False
        for q in items:
            if q.get("type") != "mc":
                continue
            options = q.get("options") or []
            correct = q.get("correct") or []
            if not options or not correct:
                continue
            before[correct[0]] += 1

            order = list(range(len(options)))
            random.Random(q["id"]).shuffle(order)
            q["options"] = [options[i] for i in order]
            q["correct"] = sorted(order.index(i) for i in correct)
            after[q["correct"][0]] += 1
            changed = True
            touched += 1
        if changed:
            file.write_text(json.dumps(items, ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")

    print(f"{touched} multiple-choice questions shuffled")
    print("position of the correct answer before:",
          {k: before[k] for k in sorted(before)})
    print("                              after:",
          {k: after[k] for k in sorted(after)})


if __name__ == "__main__":
    main()
