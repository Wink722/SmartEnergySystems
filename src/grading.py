"""Answer evaluation: fuzzy matching for terms, keyword check for open questions."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

# German terms survive in an English lecture (Bundesnetzagentur, Bilanzkreis,
# Sekundaerregelung), so umlauts still have to fold.
UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "for", "with",
    "from", "by", "as", "is", "are", "was", "were", "be", "been", "it", "its",
    "that", "this", "these", "those", "than", "then", "so", "but", "not", "no",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must",
    "into", "over", "under", "between", "per", "which", "while", "also",
}


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "").strip().lower()
    t = t.translate(UMLAUTE)
    t = re.sub(r"[^\wäöüß\s%€/\-]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def check_cloze(answer: str, accepted: list[str]) -> tuple[bool, str | None, bool]:
    """(correct, best match, was_only_just_off)"""
    ans = normalize(answer)
    if not ans:
        return False, None, False

    best, best_score = None, 0.0
    for acc in accepted:
        target = normalize(acc)
        if not target:
            continue
        if ans == target:
            return True, acc, False
        # tolerant of typos and of substring hits
        score = _similar(ans, target)
        if target in ans or ans in target:
            score = max(score, 0.93 if len(ans) >= 4 else score)
        if score > best_score:
            best, best_score = acc, score

    if best_score >= 0.86:
        return True, best, False
    return False, best, best_score >= 0.66


def check_mc(selected: list[int], correct: list[int]) -> bool:
    return sorted(selected) == sorted(correct)


def _stem(word: str) -> str:
    w = normalize(word)
    for suf in ("ations", "ation", "ements", "ement", "ically", "ingly", "ising",
                "izing", "ised", "ized", "ing", "ies", "ers", "er", "est",
                "ed", "es", "s"):
        if len(w) > 5 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def check_keywords(answer: str, keywords: list[str]) -> dict:
    """Checks which core terms of the model answer appear in the given answer."""
    ans_norm = normalize(answer)
    ans_words = [w for w in ans_norm.split() if w not in STOP]
    ans_stems = {_stem(w) for w in ans_words}
    ans_joined = " " + ans_norm + " "

    hits, misses = [], []
    for kw in keywords:
        parts = [p for p in normalize(kw).split() if p and p not in STOP]
        if not parts:
            continue
        found = False
        if normalize(kw) and normalize(kw) in ans_norm:
            found = True
        else:
            matched = 0
            for p in parts:
                stem = _stem(p)
                if p in ans_joined or stem in ans_stems or any(
                    stem and (stem in w or w in stem) and abs(len(stem) - len(w)) <= 3
                    for w in ans_stems
                ):
                    matched += 1
            found = matched >= max(1, len(parts) - 1) if len(parts) > 1 else matched == 1
        (hits if found else misses).append(kw)

    total = len(hits) + len(misses)
    return {
        "hits": hits,
        "misses": misses,
        "score": (len(hits) / total) if total else 0.0,
        "words": len(ans_words),
    }


def suggest_grade(score: float) -> int:
    """Suggestion for the self-assessment, based on the keyword hit rate."""
    if score >= 0.7:
        return 2
    if score >= 0.35:
        return 1
    return 0
