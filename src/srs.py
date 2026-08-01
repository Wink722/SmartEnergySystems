"""Spaced repetition in cram mode (Leitner with hour-level intervals).

A question answered wrongly drops back to box 0 and returns within minutes; one
answered correctly moves up and comes back later.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

# Interval per box in hours - deliberately short, because only a few days are
# left before the exam: even the safest card returns within about two days.
BOX_HOURS = [0.1, 1.5, 5.0, 14.0, 30.0, 54.0]
MAX_BOX = len(BOX_HOURS) - 1

GRADE_WRONG, GRADE_HALF, GRADE_RIGHT = 0, 1, 2


def now() -> datetime:
    return datetime.now()


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def parse(value: str | None) -> datetime:
    if not value:
        return now() - timedelta(days=365)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return now() - timedelta(days=365)


def new_card() -> dict:
    return {"box": 0, "due": None, "seen": 0, "right": 0, "wrong": 0, "last": None}


def review(card: dict, grade: int) -> dict:
    """Reschedule a card after an answer."""
    card = dict(card)
    box = int(card.get("box", 0))

    if grade == GRADE_RIGHT:
        box = min(box + 1, MAX_BOX)
        card["right"] = card.get("right", 0) + 1
    elif grade == GRADE_HALF:
        box = max(box - 1, 0) if box > 1 else box
    else:
        box = 0
        card["wrong"] = card.get("wrong", 0) + 1

    hours = BOX_HOURS[box]
    # a little scatter, so that cards do not all fall due at the same moment
    jitter = 1.0 + random.uniform(-0.12, 0.12) if box > 0 else 1.0
    card["box"] = box
    card["due"] = iso(now() + timedelta(hours=hours * jitter))
    card["seen"] = card.get("seen", 0) + 1
    card["last"] = iso(now())
    return card


def is_due(card: dict | None, at: datetime | None = None) -> bool:
    if not card:
        return True
    return parse(card.get("due")) <= (at or now())


def status(card: dict | None) -> str:
    """new | shaky | learning | solid"""
    if not card or not card.get("seen"):
        return "new"
    box = int(card.get("box", 0))
    if box == 0:
        return "shaky"
    if box >= 4:
        return "solid"
    return "learning"


def build_queue(question_ids: list[str], cards: dict, limit: int = 40,
                include_new: bool = True) -> list[str]:
    """Queue: overdue cards first, then questions that are still new."""
    at = now()
    due, fresh = [], []
    for qid in question_ids:
        card = cards.get(qid)
        if not card or not card.get("seen"):
            fresh.append(qid)
        elif is_due(card, at):
            due.append((parse(card["due"]), int(card.get("box", 0)), qid))

    due.sort(key=lambda x: (x[1], x[0]))          # weak cards first
    queue = [qid for _, _, qid in due]
    if include_new:
        queue += fresh
    return queue[:limit]


def counts(question_ids: list[str], cards: dict) -> dict:
    at = now()
    out = {"new": 0, "shaky": 0, "learning": 0, "solid": 0, "due": 0}
    for qid in question_ids:
        card = cards.get(qid)
        out[status(card)] += 1
        if card and card.get("seen") and is_due(card, at):
            out["due"] += 1
    return out


def mastery(question_ids: list[str], cards: dict) -> float:
    """Mastery 0..1, weighted by Leitner box."""
    if not question_ids:
        return 0.0
    total = sum(min(int(cards.get(q, {}).get("box", 0)), MAX_BOX) for q in question_ids)
    return total / (len(question_ids) * MAX_BOX)
