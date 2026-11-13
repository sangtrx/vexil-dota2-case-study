"""Render REPORT.md to a print-ready A4 PDF, locally (no GitHub Actions).

Requires Python mistune==3.4.0 and system Chrome/Chromium.
This is an authoring utility; the self-contained modelling notebook does not use it.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

import mistune


def render(report: Path, output: Path) -> None:
    root = report.resolve().parent
    css = (root / "scripts/report.css").read_text(encoding="utf8")
    markdown = report.read_text(encoding="utf8")
    body = mistune.create_markdown(plugins=["table"])(markdown)
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise RuntimeError("Chrome/Chromium required to render the report locally")
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    # Keep the temporary HTML beside the report so relative figure paths resolve.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", prefix=".report-preview-",
        dir=root, encoding="utf8", delete=False
    ) as temp:
        temp.write('<!doctype html><html lang="en"><head><meta charset="utf-8">')
        temp.write('<title>Live Dota 2 Win Probability</title><style>')
        temp.write(css)
        temp.write('</style></head><body>')
        temp.write(body)
        temp.write('</body></html>')
        html = Path(temp.name)
    try:
        subprocess.run([
            chrome, "--headless", "--no-sandbox", "--disable-gpu",
            "--disable-dev-shm-usage", "--no-pdf-header-footer",
            "--print-to-pdf=" + str(output), html.as_uri()
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
           text=True, check=True, timeout=100)
    finally:
        html.unlink(missing_ok=True)

    if not output.is_file() or output.stat().st_size < 10000:
        raise RuntimeError("Report render did not produce a usable PDF")

    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        info = subprocess.check_output([pdfinfo, str(output)], text=True)
        pages = next(
            (int(line.split(":", 1)[1]) for line in info.splitlines()
             if line.startswith("Pages:")), None
        )
        if pages is None or not (1 <= pages <= 4):
            raise RuntimeError(f"Report violates Vexil four-page budget: {pages}")
        print(f"Report A4 PDF: {pages} pages | {output}")
    else:
        print(f"Rendered PDF; page count needs external verification: {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1] / "REPORT.md")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "REPORT.pdf")
    args = parser.parse_args()
    render(args.report, args.output)


if __name__ == "__main__":
    main()
