# Smart Energy Infrastructure — study app

A study app for the lecture **“Smart Energy Infrastructure”** (KIT, winter term
2025/26), held by three lecturers: Dr. Dr. Andrej Pustišek (gas, oil and
infrastructure), Dr. Armin Ardone (power systems analysis, IIP) and Julia Schuler
(hydrogen and derivatives).

It covers the **642 content slides** of all six decks: first explain, then ask, then
repeat exactly what has not stuck — with the original slide beside every question.

---

## What the app can do

**Past exams** — the most important part before the exam. All **36 questions from
the two memory protocols** (WS 22/23 and WS 25/26) and from the **official example
exercise**, each with how often the topic came up, a model answer built from the
lecture slides, and the slides the answer rests on. Go through them in order, only
the frequent ones, or only what is not solid yet. These questions are flagged
everywhere in the app, and slides that carry one show a marker in Study.

**Study** — the way in when you do not know the material yet.
Chapter → section → slide by slide: the original slide on the left, its key points
in clear language on the right, and the questions on that slide directly beneath.
Every section opens with a short orientation, every chapter with a through-line.

**Practice** — spaced repetition in cram mode (Leitner, 6 boxes).
Wrong answers come back within minutes, solid ones after at most about two days —
the intervals are deliberately short because the run-up is short. Filterable by
chapter, question type and status (new / shaky / due).

**Mock exam** — 90 minutes, like the real exam, with a drawn set of tasks and a
breakdown by chapter. In the exam-like mode half of the open tasks come from the
memory protocols.

**Not exam-relevant** — every question can be switched off. It then disappears from
Practice and the mock exam and stops counting towards progress. Settings lists
everything you switched off and takes it back, singly or all at once. Past-exam
questions cannot be switched off — those provably came up.

**Script** — all six decks merged into one continuous PDF of **736 pages**: page
through it, jump to a chapter, download a single slide or the whole script.

**Glossary & search** — **101 technical terms** with definition and slide
reference, plus a full-text search across every question, model answer and slide
text.

**Statistics** — hit rate, card status, progress per chapter, a 21-day study
heatmap, daily streak.

**Ask about it** — under every revealed question sits the complete context, ready
to copy: slide text, question, model answer, core terms and your own answer, as
finished text for a chat with Claude. Copy icon in the box, paste into claude.ai,
write your question at the end. No API key, no extra cost.

---

## The question catalogue

**796 questions**, of which 760 come from the slides and 36 from the past exams.
The emphasis is deliberately on open questions, because the exam is written and
open — multiple choice and cloze exist for fast repetition and term security.

| Type | Count | Marking |
|---|---|---|
| Open questions | 481 | keyword check + self-assessment |
| Multiple choice | 125 | automatic |
| Fill in the term (cloze) | 154 | fuzzy matching, tolerant of typos and missing umlauts |

**318 graphic questions** show the original slide with the question — for the LNG
cost split, the merit order, the convolution steps, the flexibility diagrams, the
planning-tasks figure and the big comparison table of hydrogen derivatives.

| Ch | Block | Topic | Slides | Questions | of those past-exam |
|---|---|---|---|---|---|
| 1 | Gas, Oil and Infrastructure | Fundamentals of Energy Infrastructure | 82 | 82 | 7 |
| 2 | Gas, Oil and Infrastructure | Natural Gas as a Product | 24 | 27 | – |
| 3 | Gas, Oil and Infrastructure | Natural Gas Transport | 87 | 94 | 7 |
| 4 | Gas, Oil and Infrastructure | Natural Gas Storage | 72 | 91 | 7 |
| 5 | Gas, Oil and Infrastructure | Oil and Oil Products | 43 | 44 | 1 |
| 6 | Power Systems Analysis | Introduction to Energy Systems Analysis | 30 | 29 | – |
| 7 | Power Systems Analysis | Optimal Unit Commitment | 24 | 37 | 3 |
| 8 | Power Systems Analysis | Convolution | 5 | 12 | – |
| 9 | Power Systems Analysis | Capacity Expansion Planning | 35 | 58 | 1 |
| 10 | Power Systems Analysis | Scenario Planning | 26 | 31 | 1 |
| 11 | Power Systems Analysis | Investment Appraisal | 19 | 23 | – |
| 12 | Power Systems Analysis | Decision Making under Uncertainty | 21 | 21 | – |
| 13 | Power Systems Analysis | Electricity Grids | 29 | 39 | 2 |
| 14 | Hydrogen and Derivatives | Hydrogen | 61 | 71 | 4 |
| 15 | Hydrogen and Derivatives | Hydrogen Derivatives | 56 | 59 | 2 |
| 16 | Hydrogen and Derivatives | Comparison, Shipping and Metal Fuels | 28 | 42 | 1 |

### Not every slide has a question

Unlike the sister app for Innovationsmanagement, this catalogue does **not** aim at
one question per slide. **546 of the 642 content slides carry a question; 96 are
deliberately left out** — agenda and divider slides, motivational and marketing
slides, website screenshots, and the many near-identical data slides where the same
trend is asked once instead of six times.

Every one of those 96 slides sits in `data/skipped/` with a one-sentence reason:

```bash
python tools/check_questions.py --excluded
```

The checker lists uncovered slides but only treats them as an error if they are
**neither covered nor on the exclusion list**.

---

## Progress

Progress goes into the browser's **LocalStorage** automatically — no login, no
account. Close the page, come back days later, carry on in the same place.

Under **Settings** the state can also be saved as a JSON file and imported on
another device or in another browser.

---

## Running it

### Locally

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

### Streamlit Community Cloud

1. Connect the repository on [share.streamlit.io](https://share.streamlit.io)
2. Main file: `app.py`
3. Deploy — `requirements.txt` is installed automatically

For a **private repository**, allow extended access (“private repositories”) when
connecting GitHub.

---

## Project structure

```
app.py                        entry point, navigation, routing
requirements.txt
smart_energy_systems.pdf      736 pages: all six decks merged
data/
  slides.json                 736 pages with chapter, part, section, title, text, graphic flag
  guide.json                  16 chapter and 80 section introductions (the learning path)
  questions/*.json            760 questions with model answers and slide reference
  pastexams/*.json            36 questions from the memory protocols and the official example
  skipped/*.json              96 deliberately uncovered slides, each with a reason
src/
  content.py                  loading and indexing
  srs.py                      spaced repetition (Leitner, hour-level)
  grading.py                  fuzzy matching and keyword check
  storage.py                  persistence in LocalStorage
  theme.py                    design system (light/dark)
  ui.py, qcard.py             interface building blocks, question rendering
  view_recall.py              the Past exams area
  view_*.py                   the remaining views
tools/
  build_slides.py             merges the decks, writes data/slides.json
  render_slides.py            renders the content slides to PNG (authoring aid)
  check_questions.py          checks coverage, ids, slide references, keywords
  check_block.py              the same, scoped to one authoring block
  shuffle_mc.py               shuffles the multiple-choice options
```

Rebuild the script and the slide data (only needed if a deck is replaced — expects
the source PDFs in `../files`):

```bash
python tools/build_slides.py
```

Check the catalogue:

```bash
python tools/check_questions.py
```

---

## Notes on the material

- The decks carry **no PDF outline**, so slide titles cannot be read from
  bookmarks. `build_slides.py` recovers them from the layout instead: every deck
  prints the slide number on its own line, and the title is the run of equally
  sized lines that follows it. The printed number rarely matches the PDF page —
  part 2 keeps counting where part 1 stopped — so the offset is settled per deck
  by majority vote.
- The past-exam questions come from the **two memory protocols** (WS 22/23 and
  WS 25/26) and the **official example exercise** handed out for 25/26. Frequency
  and the “very frequent” marking follow the protocols; the model answers are
  worked out from the lecture slides. Where a protocol question has no solid basis
  in the slides, the question says so.
- **The slides contradict themselves in a number of places.** Every question gives
  the factually correct version and points out the discrepancy. The most important
  ones: the control-reserve figure labels the secondary band “Primary control”; the
  hydrogen exercise sheet writes MWh where kWh is meant; slide 643 claims 45 % of
  global hydrogen demand goes to ammonia, which does not square with the deck's own
  150 Mt/a and 0.18 kg H₂/kg NH₃; the methanol synthesis enthalpy and the methanol
  cracking conditions are copy-pasted from the ammonia slides; global hydrogen
  production is given as 100, 110 and 120 Mt/a on three different slides.
- The Leitner intervals are set for a **ten-day run-up**: 6 minutes, 1.5 h, 5 h,
  14 h, 30 h, 54 h. Even the safest card returns within about two days.

---

## Basis

Lecture slides “Smart Energy Infrastructure”, KIT, winter term 2025/26 —
Dr. Dr. Andrej Pustišek, Dr. Armin Ardone (Institute for Industrial Production,
Chair of Energy Economics) and Julia Schuler.

Questions and model answers were written from the original slides; every question
links back to the slide it came from.
