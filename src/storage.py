"""Persistent study progress without a login.

Everything is written to the browser's LocalStorage, which survives closing the
tab, restarting the browser and any number of days.

Two Streamlit quirks shape this module:

1. A script run that ends in ``st.rerun()`` sends nothing to the browser -
   everything rendered during that run is discarded. The write therefore has to
   happen at the very *end* of ``main()``: only runs that get that far talk to
   the browser at all, and the run following a rerun stores the current state.
2. The LocalStorage component hands JSON values back already parsed as a dict,
   not as a string. Older versions returned a string, so both are accepted.

On top of that: a local backup file (where the filesystem is writable) and
export/import as JSON.
"""

from __future__ import annotations

import base64
import json
import zlib
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

KEY = "ses_progress_v1"
LOCAL_FILE = Path(__file__).resolve().parents[1] / ".progress.json"
SCHEMA = 1


def blank(name: str = "") -> dict:
    return {
        "v": SCHEMA,
        "rev": 0,
        "name": name,
        "created": date.today().isoformat(),
        "cards": {},        # qid -> Leitner card
        "learned": {},      # slide number (str) -> timestamp
        "skipped": {},      # qid -> timestamp: marked as not exam-relevant
        "days": {},         # YYYY-MM-DD -> {answered, right, learned}
        "streak": {"current": 0, "best": 0, "last_day": ""},
        "exam_date": "",
        "goal": 60,
        "theme": "light",
        "exams": [],
    }


def _merge(data: dict) -> dict:
    base = blank()
    if not isinstance(data, dict):
        return base
    base.update({k: v for k, v in data.items() if k in base})
    for key in ("cards", "learned", "days", "streak", "skipped"):
        if not isinstance(base.get(key), dict):
            base[key] = blank()[key]
    if not isinstance(base.get("exams"), list):
        base["exams"] = []
    return base


# ------------------------------------------------------------------ reading

def _read_localstorage():
    """Read every LocalStorage entry. None = the browser has not answered yet."""
    try:
        from streamlit_local_storage import _st_local_storage
    except Exception:
        return {}
    try:
        return _st_local_storage(method="getAll", key="ses_ls_read", default=None)
    except Exception:
        return {}


def boot() -> dict | None:
    """Load progress once per session. None -> the browser is still answering."""
    if "progress" in st.session_state:
        return st.session_state["progress"]

    items = _read_localstorage()
    if items is None and not st.session_state.get("_ls_give_up"):
        return None

    data = None
    if isinstance(items, dict):
        raw = items.get(KEY)
        # The component returns JSON values already parsed as a dict; older
        # versions returned a string - accept both.
        if isinstance(raw, dict):
            data = raw
        elif isinstance(raw, str) and raw.strip():
            try:
                data = json.loads(raw)
            except Exception:
                data = None

    if data is None and LOCAL_FILE.exists():
        try:
            data = json.loads(LOCAL_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = None

    st.session_state["progress"] = _merge(data or {})
    st.session_state["restored"] = bool(data)
    return st.session_state["progress"]


def load() -> dict:
    return st.session_state.get("progress") or blank()


# ------------------------------------------------------------------ writing

def mirror() -> None:
    """Write the current state to LocalStorage.

    Must be called at the very end of the script run - see the module comment.
    """
    p = st.session_state.get("progress")
    if not p:
        return

    payload = json.dumps(p, ensure_ascii=False, separators=(",", ":"))
    if payload == st.session_state.get("_mirrored"):
        # Unchanged: still render, so the iframe stays stable, but do not
        # write again.
        components.html("<span></span>", height=0)
        return

    encoded = base64.b64encode(payload.encode("utf-8")).decode("ascii")
    components.html(
        f"""<script>
try {{
  var store = (window.parent && window.parent.localStorage) || localStorage;
  var text = decodeURIComponent(escape(window.atob("{encoded}")));
  store.setItem("{KEY}", text);
  store.removeItem("undefined");
}} catch (e) {{ /* private mode or similar - export/import remains as a way out */ }}
</script>""",
        height=0,
    )
    st.session_state["_mirrored"] = payload

    try:
        LOCAL_FILE.write_text(payload, encoding="utf-8")
    except Exception:
        pass


def is_skipped(p: dict, qid: str) -> bool:
    return qid in (p.get("skipped") or {})


def toggle_skip(p: dict, qid: str) -> bool:
    """Mark a question as not exam-relevant, or take it back. True = now off."""
    skipped = p.setdefault("skipped", {})
    if qid in skipped:
        skipped.pop(qid, None)
        touch()
        return False
    skipped[qid] = datetime.now().replace(microsecond=0).isoformat()
    touch()
    return True


def touch() -> None:
    """Marks the state as changed (bumps the revision)."""
    p = st.session_state.get("progress")
    if p:
        p["rev"] = int(p.get("rev", 0)) + 1


# ----------------------------------------------------------- daily statistics

def today() -> str:
    return date.today().isoformat()


def day_entry(p: dict, day: str | None = None) -> dict:
    day = day or today()
    entry = p["days"].setdefault(day, {"answered": 0, "right": 0, "learned": 0})
    for field in ("answered", "right", "learned"):
        entry.setdefault(field, 0)
    return entry


def record_answer(p: dict, correct: bool) -> None:
    entry = day_entry(p)
    entry["answered"] += 1
    entry["right"] += 1 if correct else 0
    bump_streak(p)
    touch()


def record_learned(p: dict, page: int) -> bool:
    """Mark a slide as studied. True if it was new."""
    key = str(page)
    if key in p["learned"]:
        return False
    p["learned"][key] = datetime.now().replace(microsecond=0).isoformat()
    day_entry(p)["learned"] += 1
    bump_streak(p)
    touch()
    return True


def bump_streak(p: dict) -> None:
    s = p["streak"]
    t = today()
    if s.get("last_day") == t:
        return
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    s["current"] = s.get("current", 0) + 1 if s.get("last_day") == yesterday else 1
    s["best"] = max(s.get("best", 0), s["current"])
    s["last_day"] = t


def streak_value(p: dict) -> int:
    """The streak that still counts today (studying yesterday keeps it alive)."""
    s = p.get("streak", {})
    last = s.get("last_day", "")
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if last in (today(), yesterday):
        return int(s.get("current", 0))
    return 0


def days_left(p: dict) -> int | None:
    if not p.get("exam_date"):
        return None
    try:
        target = date.fromisoformat(p["exam_date"])
    except ValueError:
        return None
    return (target - date.today()).days


# ----------------------------------------------------------- export / import

def export_bytes(p: dict) -> bytes:
    return json.dumps(p, ensure_ascii=False, indent=1).encode("utf-8")


def export_code(p: dict) -> str:
    raw = json.dumps(p, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii")


def import_payload(text: str) -> dict | None:
    text = (text or "").strip()
    if not text:
        return None
    try:
        return _merge(json.loads(text))
    except Exception:
        pass
    try:
        raw = zlib.decompress(base64.urlsafe_b64decode(text.encode("ascii")))
        return _merge(json.loads(raw.decode("utf-8")))
    except Exception:
        return None
