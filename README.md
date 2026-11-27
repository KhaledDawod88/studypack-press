# StudyPack Press

**StudyPack Press turns an open course curriculum into a print-ready study pack: one PDF, one page per topic, with a cover, a contents page, formula cards, worked examples and a one-page formula sheet at the back.**

Students do not need another feed. They need one clean artifact they can print, fold and carry into an exam. Open curricula such as OpenStax are free and excellent, but they are long, and the week before an exam is the worst time to be scrolling a 900-page textbook. This repo is the small pipeline that compresses a course into pages a student can actually use.

The sample in `samples/` is built from the opening chapters of OpenStax *Introductory Statistics 2e*: six topics, nine pages.

![Cover](samples/preview-cover.png)

## What a pack contains

| Page | Content |
| --- | --- |
| 1 | Cover: course code, level, edition, the source curriculum and its licence |
| 2 | Contents with real page numbers, a topic map, and how to use the pack |
| 3 onward | One page per topic: objectives, the idea in one paragraph, key ideas, formula cards, one worked example, common mistakes, three self-check questions with answers |
| Last | One-page formula sheet: every formula in the course, plus "which test when", assumptions to state, and a notation key |

Each topic page is deliberately one page. If a topic grows past that, the build says so instead of silently spilling onto a second page.

![A topic page](samples/preview-topic.png)

## Quick start

```bash
python3 tools/fetch_fonts.sh                      # optional: the three typefaces
python3 build.py configs/intro-statistics.json    # writes build/studypack-intro-statistics.pdf
```

Preview PNGs of any pages:

```bash
python3 build.py configs/intro-statistics.json --preview-pages 1,3,9
```

Requirements: Python 3.9 or newer, and Chrome or Chromium on the PATH. Nothing else is required to get a PDF. If `reportlab` and `pypdf` (or `qpdf`) are installed, the build also stamps the footer rule and the page numbers; without them you still get the full document, just without the footer. `pdftoppm` from poppler-utils is only needed for previews.

## The two files you edit

A course is a pair of JSON files, so a new subject never means touching code.

`configs/intro-statistics.json` decides **how it is built**:

```json
{
  "content": "content/intro-statistics.json",
  "output": "build/studypack-intro-statistics.pdf",
  "theme_file": "theme/pack.css",
  "paper": "A4",
  "paper_width_mm": 210,
  "paper_height_mm": 297,
  "include_cheatsheet": true,
  "footer": { "left": "STAT 101 · Introduction to Statistics · study pack",
              "right": "page {n} of {total}" },
  "theme": { "accent": "#1d4ed8", "deep": "#101a3d", "ink": "#151a2b",
             "muted": "#5b6478", "rule": "#d5dae5", "paper": "#fdfcf9", "tint": "#eef2fb" }
}
```

`content/intro-statistics.json` holds **what goes on the pages**:

```json
{
  "course": { "code": "STAT 101", "title": "…", "subtitle": "…", "level": "…",
              "edition": "…", "source": { "name": "…", "url": "…", "license": "CC BY 4.0" },
              "alignment": "…" },
  "sections": [
    { "id": "…", "kicker": "Topic 1", "title": "…", "map_label": "…",
      "objectives": ["…"],
      "lead": "…",
      "key_ideas": ["…"],
      "formulas": [{ "label": "…", "expr": "…", "note": "…" }],
      "example": { "title": "Worked example", "problem": "…", "steps": ["…"],
                   "answer": "…", "takeaway": "…" },
      "pitfalls": ["…"],
      "check": [{ "q": "…", "a": "…" }] }
  ],
  "cheatsheet": [
    { "group": "Describing data", "column": 1, "items": [{ "label": "…", "expr": "…" }] },
    { "group": "Which test when", "column": 2, "kind": "pairs", "items": [{ "label": "…", "expr": "…" }] },
    { "group": "Assumptions to state", "column": 2, "kind": "list", "items": ["…"] }
  ],
  "reference_values": [{ "label": "…", "value": "…" }]
}
```

`kind` is `formula` (default), `pairs` or `list`; `column` is 1 or 2. To build a different course, copy both files, change the content, and point the config at the new pair.

## How the render works

1. `build.py` assembles one HTML document: paged-media CSS from `theme/pack.css`, with the config's colour tokens substituted in.
2. Headless Chrome prints it to A4 (`--print-to-pdf`), so the same HTML is also a readable web page.
3. A footer rule and "page n of total" are drawn with reportlab and merged with pypdf (or `qpdf --overlay`), because Chrome cannot draw page numbers in the margin.
4. Page numbers in the contents are computed from the document structure, and the build checks the rendered page count against the plan. A mismatch means a topic overflowed, and the build tells you instead of shipping a broken contents page.

The cover artwork is generated, not drawn by hand: the bars are a normal density with a second small bump, and the curve over them is the same function, computed in `cover_art()`.

![The formula sheet](samples/preview-formula-sheet.png)

## Free tools only

Python standard library, headless Chrome, reportlab, pypdf or qpdf, poppler-utils, and three typefaces under the SIL Open Font License (Source Serif 4, Inter, JetBrains Mono). No paid service, no API key, no account, nothing to sign up for. `tools/fetch_fonts.sh` downloads the fonts from the Google Fonts repository; without them the pack falls back to Georgia, Arial and DejaVu, which is close but not identical.

## Automation

`.github/workflows/build.yml` rebuilds the sample on every push that touches the content, config or theme, and uploads the PDF as a workflow artifact. It needs no secrets: it uses the Chrome that ships on GitHub's Ubuntu runners.

## Adding a course

1. `cp configs/intro-statistics.json configs/<course>.json` and `cp content/intro-statistics.json content/<course>.json`.
2. Point `content` in the new config at the new content file, and change `output`.
3. Fill in the sections. Keep each one to a page: about three objectives, six or seven key ideas, two or three formula cards, one worked example, three pitfalls, three checks.
4. Run the build. If it warns about the page count, trim the longest section.

The content in `content/` is written from the open curriculum named in the `source` field, with its licence recorded on the cover. If you reuse someone else's text, keep the attribution and check the licence.

## Licence

MIT for the code. The sample content is derived from OpenStax *Introductory Statistics 2e*, CC BY 4.0, and keeps that attribution on the cover and in this README.
