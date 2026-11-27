#!/usr/bin/env python3
"""
StudyPack Press: turn an open course curriculum into a print-ready study pack.

    python3 build.py configs/intro-statistics.json
    python3 build.py configs/intro-statistics.json --preview-pages 1,3

What happens:
  1. read the build config (configs/*.json) and the course content it points at
  2. render one paged HTML document (theme/pack.css, paged media)
  3. print it to PDF with headless Chrome
  4. stamp the footer rule and page numbers (reportlab + pypdf or qpdf)
  5. optionally export PNG page previews (pdftoppm)

Free tools only. Python standard library for the build, plus reportlab and
pypdf/qpdf for the footer stamp, headless Chrome for the print, pdftoppm for
previews. Every one of those is optional except Chrome: the build degrades to
an unstamped PDF rather than failing.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def esc(text: str) -> str:
    """Escape text but keep the small amount of inline markup the content uses."""
    keep = {"<b>", "</b>", "<i>", "</i>", "<br>", "<span class=\"hl\">", "</span>"}
    out = html.escape(str(text), quote=False)
    for tag in keep:
        out = out.replace(html.escape(tag, quote=False), tag)
    return out


def find_chrome() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        path = shutil.which(name)
        if path:
            return path
    raise SystemExit(
        "No Chrome or Chromium found. Install Google Chrome, or set CHROME=/path/to/chrome."
    )


def count_pages(pdf: Path) -> int:
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf)).pages)
    except Exception:
        pass
    for cmd in (["pdfinfo"], ["qpdf", "--show-npages"]):
        if not shutil.which(cmd[0]):
            continue
        res = subprocess.run(cmd + [str(pdf)], capture_output=True, text=True)
        if res.returncode != 0:
            continue
        if cmd[0] == "pdfinfo":
            for line in res.stdout.splitlines():
                if line.lower().startswith("pages:"):
                    return int(line.split()[1])
        else:
            return int(res.stdout.strip())
    return 0


def overlay_pdfs(base: Path, over: Path, out: Path) -> bool:
    """Draw `over` on top of `base`."""
    try:
        from pypdf import PdfReader, PdfWriter  # type: ignore

        overlay = PdfReader(str(over))
        writer = PdfWriter(clone_from=str(base))
        for i, page in enumerate(writer.pages):
            page.merge_page(overlay.pages[i])
        with open(out, "wb") as handle:
            writer.write(handle)
        return True
    except ImportError:
        pass
    if shutil.which("qpdf"):
        res = subprocess.run(
            ["qpdf", "--overlay", str(over), "--", str(base), str(out)],
            capture_output=True,
            text=True,
        )
        return res.returncode == 0
    return False


# --------------------------------------------------------------------------- #
# cover artwork: a distribution motif drawn from the same maths as the content
# --------------------------------------------------------------------------- #

def cover_art(accent: str, deep: str) -> str:
    width, height, base = 1000, 300, 250
    bars, curve = [], []
    for i in range(56):
        x = 40 + i * 16.4
        t = (i - 27.5) / 9.0
        y = math.exp(-0.5 * t * t) * 0.86 + 0.14 * math.exp(-0.5 * ((t - 1.6) / 0.55) ** 2)
        h = y * 200
        bars.append(
            f'<rect x="{x:.1f}" y="{base - h:.1f}" width="9.5" height="{h:.1f}" '
            f'rx="1.2" fill="{accent}" opacity="0.16"/>'
        )
    for i in range(120):
        x = 40 + i * 7.63
        t = (x - 40 - 0.5 * 56 * 16.4) / (9.0 * 16.4)
        y = base - (math.exp(-0.5 * t * t) * 0.86) * 200
        curve.append(f"{x:.1f},{y:.1f}")
    return f"""<svg class="cover-art" viewBox="0 0 {width} {height}" preserveAspectRatio="none" aria-hidden="true">
  {''.join(bars)}
  <polyline points="{' '.join(curve)}" fill="none" stroke="{deep}" stroke-width="2.4" stroke-linejoin="round"/>
  <line x1="40" y1="{base}" x2="960" y2="{base}" stroke="{deep}" stroke-width="1.2" opacity="0.55"/>
  <line x1="{40 + 18.5 * 16.4:.1f}" y1="{base - 190}" x2="{40 + 18.5 * 16.4:.1f}" y2="{base}" stroke="{accent}" stroke-width="1.4" stroke-dasharray="6 5" opacity="0.75"/>
  <circle cx="{40 + 18.5 * 16.4:.1f}" cy="{base - 190}" r="5" fill="{accent}"/>
</svg>"""


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #

def render_html(cfg: dict, content: dict) -> str:
    theme = cfg["theme"]
    css = (ROOT / cfg["theme_file"]).read_text(encoding="utf-8")
    css = css.replace("{{accent}}", theme["accent"]).replace("{{deep}}", theme["deep"])
    css = css.replace("{{paper}}", theme["paper"]).replace("{{ink}}", theme["ink"])
    css = css.replace("{{muted}}", theme["muted"]).replace("{{rule}}", theme["rule"])
    css = css.replace("{{tint}}", theme["tint"])

    course = content["course"]
    sections = content["sections"]
    first_page_of = lambda i: 3 + i  # cover 1, contents 2, topics from 3
    has_cheat = bool(content.get("cheatsheet")) and cfg.get("include_cheatsheet", True)

    parts: list[str] = []

    # cover -------------------------------------------------------------- #
    parts.append(
        f"""<section class="cover">
  <div class="cover-inner">
    <div class="eyebrow">{esc(cfg.get('cover_eyebrow', 'Study pack'))}</div>
    <h1 class="cover-title">{esc(course['title'])}</h1>
    <p class="cover-sub">{esc(course['subtitle'])}</p>
    <div class="cover-meta">
      <span class="chip">{esc(course['code'])}</span>
      <span class="chip">{esc(course['level'])}</span>
      <span class="chip">{esc(course['edition'])}</span>
    </div>
  </div>
  {cover_art(theme['accent'], theme['deep'])}
  <div class="cover-foot">
    <span>Built from {esc(course['source']['name'])} ({esc(course['source']['license'])})</span>
    <span>{len(sections)} topics &middot; {len(sections) + (3 if has_cheat else 2)} pages</span>
  </div>
</section>"""
    )

    # contents ----------------------------------------------------------- #
    rows = []
    for i, section in enumerate(sections):
        rows.append(
            f"""<li class="toc-row">
      <span class="toc-num">{i + 1:02d}</span>
      <span class="toc-title">{esc(section['title'])}</span>
      <span class="toc-dots"></span>
      <span class="toc-page">{first_page_of(i)}</span>
    </li>"""
        )
    if has_cheat:
        rows.append(
            f"""<li class="toc-row">
      <span class="toc-num">&mdash;</span>
      <span class="toc-title">One-page formula sheet</span>
      <span class="toc-dots"></span>
      <span class="toc-page">{first_page_of(len(sections))}</span>
    </li>"""
        )
    map_rows = ""
    for row_start in (0, 3):
        row = sections[row_start:row_start + 3]
        if not row:
            continue
        cells = []
        for offset, section in enumerate(row):
            if offset:
                cells.append('<div class="map-arrow">&#8594;</div>')
            cells.append(
                f'<div class="map-node"><span class="n">{row_start + offset + 1:02d}</span>'
                f'<span class="t">{esc(section.get("map_label", section["title"]))}</span></div>'
            )
        map_rows += '<div class="map-row">' + "".join(cells) + "</div>"

    parts.append(
        f"""<section class="contents">
  <h2 class="page-title">Contents</h2>
  <p class="contents-note">{esc(course['alignment'])}</p>
  <ol class="toc">{''.join(rows)}</ol>
  <div class="map">
    <div class="lbl">How the six topics connect</div>
    {map_rows}
  </div>
  <div class="how-to">
    <div class="how-to-item"><span class="lbl">How to use this pack</span>
      Read one topic, then close the pack and say the three objectives out loud. Open it again only for the
      formula cards and the self-check.</div>
    <div class="how-to-item"><span class="lbl">What each page holds</span>
      Objectives, the idea in one paragraph, key ideas, formula cards, one worked example, common mistakes,
      and three questions with answers.</div>
  </div>
  <div class="rebuild">
    <div class="lbl">Rebuild this pack</div>
    <pre>python3 tools/fetch_fonts.sh
python3 build.py configs/intro-statistics.json</pre>
    <p>Swap the course by editing the pair of JSON files: <span class="mono">configs/</span> holds the paper,
    footer and accent, <span class="mono">content/</span> holds the material. One topic is one page, and the
    build tells you when a topic no longer fits.</p>
  </div>
</section>"""
    )

    # topics ------------------------------------------------------------- #
    for i, section in enumerate(sections):
        objectives = "".join(f"<li>{esc(o)}</li>" for o in section["objectives"])
        ideas = "".join(f"<li>{esc(k)}</li>" for k in section["key_ideas"])
        cards = "".join(
            f"""<div class="fcard">
        <div class="lbl">{esc(f['label'])}</div>
        <div class="ex">{esc(f['expr'])}</div>
        <div class="note">{esc(f['note'])}</div>
      </div>"""
            for f in section["formulas"]
        )
        steps = "".join(f"<li>{esc(s)}</li>" for s in section["example"]["steps"])
        pitfalls = "".join(f"<li>{esc(p)}</li>" for p in section["pitfalls"])
        checks = "".join(
            f"""<li><span class="q">{esc(c['q'])}</span>
        <span class="a">{esc(c['a'])}</span></li>"""
            for c in section["check"]
        )
        parts.append(
            f"""<section class="topic">
  <header class="topic-head">
    <div class="num">{i + 1:02d}</div>
    <div class="head-text">
      <div class="kicker">{esc(section['kicker'])} of {len(sections)}</div>
      <h2>{esc(section['title'])}</h2>
    </div>
  </header>
  <div class="objectives">
    <div class="lbl">By the end of this page you can</div>
    <ul>{objectives}</ul>
  </div>
  <p class="lead">{esc(section['lead'])}</p>
  <div class="lbl section-lbl">Key ideas</div>
  <ul class="ideas">{ideas}</ul>
  <div class="formulas">{cards}</div>
  <div class="example">
    <div class="lbl">{esc(section['example']['title'])}</div>
    <p class="problem">{esc(section['example']['problem'])}</p>
    <ol class="steps">{steps}</ol>
    <p class="answer">{esc(section['example']['answer'])}</p>
    <p class="takeaway">{esc(section['example']['takeaway'])}</p>
  </div>
  <div class="bottom">
    <div class="pitfalls">
      <div class="lbl">Common mistakes</div>
      <ul>{pitfalls}</ul>
    </div>
    <div class="check">
      <div class="lbl">Check yourself</div>
      <ol>{checks}</ol>
    </div>
  </div>
</section>"""
        )

    # formula sheet ------------------------------------------------------ #
    if has_cheat:
        def group_html(group: dict) -> str:
            kind = group.get("kind", "formula")
            if kind == "list":
                body = "".join(f"<li>{esc(x)}</li>" for x in group["items"])
                return (
                    f'<div class="cheat-group"><div class="lbl">{esc(group["group"])}</div>'
                    f'<ul class="cheat-list">{body}</ul></div>'
                )
            cls = "cheat-pair" if kind == "pairs" else "cheat-item"
            items = "".join(
                f'<div class="{cls}"><span class="cheat-lbl">{esc(i["label"])}</span>'
                f'<span class="cheat-ex">{esc(i["expr"])}</span></div>'
                for i in group["items"]
            )
            return f'<div class="cheat-group"><div class="lbl">{esc(group["group"])}</div>{items}</div>'

        columns: dict[int, list[str]] = {}
        for group in content["cheatsheet"]:
            columns.setdefault(int(group.get("column", 1)), []).append(group_html(group))
        col_html = "".join(
            f'<div class="cheat-col">{"".join(columns[key])}</div>' for key in sorted(columns)
        )
        refs = "".join(
            f"""<div class="ref"><span class="cheat-lbl">{esc(r['label'])}</span>
        <span class="ref-val">{esc(r['value'])}</span></div>"""
            for r in content.get("reference_values", [])
        )
        parts.append(
            f"""<section class="cheat">
  <header class="topic-head">
    <div class="num">&mdash;</div>
    <div class="head-text">
      <div class="kicker">Reference</div>
      <h2>One-page formula sheet</h2>
    </div>
  </header>
  <div class="cheat-grid">{col_html}</div>
  <div class="refs">{refs}</div>
</section>"""
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{esc(course['code'])} {esc(course['title'])} &middot; Study pack</title>
<meta name="author" content="StudyPack Press">
<meta name="description" content="{esc(course['subtitle'])}">
<style>{css}</style>
</head>
<body>
{''.join(parts)}
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #

def print_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = find_chrome()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=15000",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        html_path.as_uri(),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if not pdf_path.exists():
        raise SystemExit(f"Chrome did not write a PDF.\n{res.stderr[-2000:]}")


def stamp_footers(pdf_path: Path, left: str, right_template: str, size: tuple) -> bool:
    try:
        from reportlab.lib.units import mm  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore
    except ImportError:
        return False
    total = count_pages(pdf_path)
    if not total:
        return False
    overlay = pdf_path.with_suffix(".overlay.pdf")
    sheet = canvas.Canvas(str(overlay), pagesize=size)
    for page in range(1, total + 1):
        if page > 1:  # the cover carries no footer
            sheet.setFillGray(0.42)
            sheet.setFont("Helvetica", 7.4)
            sheet.drawString(15 * mm, 10.6 * mm, left)
            sheet.drawRightString(size[0] - 15 * mm, 10.6 * mm, right_template.format(n=page, total=total))
            sheet.setStrokeGray(0.86)
            sheet.setLineWidth(0.3)
            sheet.line(15 * mm, 14 * mm, size[0] - 15 * mm, 14 * mm)
        sheet.showPage()
    sheet.save()
    merged = pdf_path.with_suffix(".stamped.pdf")
    if overlay_pdfs(pdf_path, overlay, merged):
        merged.replace(pdf_path)
        overlay.unlink(missing_ok=True)
        return True
    overlay.unlink(missing_ok=True)
    return False


def export_previews(pdf_path: Path, pages: list[int], out_dir: Path, stem: str, dpi: int) -> list[Path]:
    if not shutil.which("pdftoppm"):
        return []
    written = []
    for page in pages:
        target = out_dir / f"{stem}-p{page}"
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page), str(pdf_path), str(target)],
            check=False,
        )
        for produced in out_dir.glob(f"{stem}-p{page}-*.png"):
            final = out_dir / f"{stem}-p{page}.png"
            produced.replace(final)
            written.append(final)
    return written


# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Build a study pack PDF from a course config.")
    parser.add_argument("config", help="path to configs/<course>.json")
    parser.add_argument("--out", default=None, help="override the output PDF path")
    parser.add_argument("--preview-pages", default="", help="comma-separated page numbers to export as PNG")
    parser.add_argument("--preview-dpi", type=int, default=110)
    parser.add_argument("--no-stamp", action="store_true", help="skip the footer and page numbers")
    parser.add_argument("--report", action="store_true", help="print a JSON build report")
    args = parser.parse_args()

    config_path = (ROOT / args.config).resolve()
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    content_path = (ROOT / cfg["content"]).resolve()
    content = json.loads(content_path.read_text(encoding="utf-8"))

    pdf_path = Path(args.out) if args.out else (ROOT / cfg["output"])
    pdf_path = pdf_path if pdf_path.is_absolute() else (ROOT / pdf_path)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = pdf_path.with_suffix(".html")

    html_path.write_text(render_html(cfg, content), encoding="utf-8")
    print(f"html   {html_path.relative_to(ROOT)}")
    print_pdf(html_path, pdf_path)
    pages = count_pages(pdf_path)

    expected = 2 + len(content["sections"]) + (1 if content.get("cheatsheet") else 0)
    if pages and pages != expected:
        print(
            f"warn   {pages} pages rendered, {expected} planned. A topic overflowed its page: "
            "trim the content or tighten theme/pack.css.",
            file=sys.stderr,
        )

    stamped = False
    if not args.no_stamp:
        stamped = stamp_footers(
            pdf_path,
            cfg["footer"]["left"],
            cfg["footer"]["right"],
            (cfg["paper_width_mm"] * 2.834645669, cfg["paper_height_mm"] * 2.834645669),
        )
        if not stamped:
            print("warn   footer stamp skipped (reportlab and pypdf or qpdf not available)", file=sys.stderr)

    previews = []
    if args.preview_pages:
        wanted = [int(p) for p in args.preview_pages.split(",") if p.strip()]
        previews = export_previews(pdf_path, wanted, pdf_path.parent, pdf_path.stem, args.preview_dpi)

    print(f"pdf    {pdf_path.relative_to(ROOT)}  ({pages} pages, {pdf_path.stat().st_size // 1024} KB)")
    for preview in previews:
        print(f"png    {preview.relative_to(ROOT)}")

    if args.report:
        print(
            json.dumps(
                {
                    "config": str(config_path.relative_to(ROOT)),
                    "content": str(content_path.relative_to(ROOT)),
                    "pdf": str(pdf_path.relative_to(ROOT)),
                    "pages": pages,
                    "expected_pages": expected,
                    "stamped": stamped,
                    "bytes": pdf_path.stat().st_size,
                    "previews": [str(p.relative_to(ROOT)) for p in previews],
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
