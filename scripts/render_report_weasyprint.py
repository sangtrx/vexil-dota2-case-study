"""Render REPORT.md to print-ready PDF with optional WeasyPrint fallback.

Local authoring utility only: not needed to run the frozen model notebook.
Dependencies: mistune==3.4.0, weasyprint==66.0, system Pango/Cairo.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import mistune
from weasyprint import HTML, CSS


def render(report: Path, output: Path) -> None:
    report = report.resolve()
    root = report.parent
    body = mistune.create_markdown(plugins=["table"])(report.read_text(encoding="utf8"))
    image_urls = re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', body)
    if not image_urls:
        raise ValueError("Report has no embedded figures")
    for image in image_urls:
        url = urlsplit(image)
        if url.scheme or url.netloc or not (root / unquote(url.path)).is_file():
            raise ValueError(f"Report figure is not a verified local file: {image}")
    html = '<!doctype html><html lang="en"><head><meta charset="utf-8"></head><body>'+body+'</body></html>'
    css = CSS(filename=str(root / "scripts" / "report.css"))
    # A directory base URL MUST end with a slash, or relative images silently fail.
    base_url = root.as_uri().rstrip("/") + "/"
    doc = HTML(string=html, base_url=base_url).render(stylesheets=[css])
    if not 1 <= len(doc.pages) <= 4:
        raise ValueError(f"Vexil four-page budget exceeded: {len(doc.pages)} pages")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.write_pdf(output)
    print(f"Report A4 PDF: {len(doc.pages)} pages, {len(image_urls)} figures | {output}")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1] / "REPORT.md")
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "REPORT.pdf")
    args = ap.parse_args()
    render(args.report, args.output)

if __name__ == "__main__":
    main()
