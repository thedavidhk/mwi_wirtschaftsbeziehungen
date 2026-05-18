#!/usr/bin/env python3
"""Prepare script.build.md and PDF figures for the Pandoc lecture PDF."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
SCRIPT = ROOT / "script.md"
BUILD_SCRIPT = ROOT / "script.build.md"
FIG_DIR = ROOT / "build" / "figures"
FIG_SVG_DIR = ROOT / "build" / "figure-svg"
IMAGE_DIR = REPO_ROOT / "images"
GENERATE_FIGURES = REPO_ROOT / "scripts" / "generate_figures.py"

# Hand-drawn SVGs (not from generate_figures.py): lighten axis labels for print.
PRINT_SVG_REPLACEMENTS = (
    ("#e6e6e6", "#333333"),
    ("#e7e7e7", "#333333"),
    ("fill:#e6e6e6", "fill:#333333"),
    ("fill:#e7e7e7", "fill:#333333"),
)

PRINT_SVG_NAMES = frozenset(
    {
        "capital_market1",
        "capital_market2",
        "global_ca_balances",
    }
)


def generate_script_figures() -> None:
    """Regenerate matplotlib figures with light-theme axis labels for the PDF."""
    result = subprocess.run(
        [sys.executable, str(GENERATE_FIGURES), "--script"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit("generate_figures.py --script failed")


def adapt_svg_for_print(svg: Path, dest: Path) -> None:
    """Rewrite light-on-dark text colors for a white PDF background."""
    text = svg.read_text(encoding="utf-8")
    for old, new in PRINT_SVG_REPLACEMENTS:
        text = text.replace(old, new)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


def resolve_svg(name: str) -> Path:
    """Pick the best SVG source for a script figure (light theme when available)."""
    light = FIG_SVG_DIR / f"{name}.svg"
    if light.exists():
        return light
    source = IMAGE_DIR / f"{name}.svg"
    if not source.exists():
        raise SystemExit(f"Missing figure: {source}")
    if name in PRINT_SVG_NAMES:
        adapted = FIG_SVG_DIR / f"{name}.svg"
        adapt_svg_for_print(source, adapted)
        return adapted
    return source


def convert_svg(svg: Path, pdf: Path) -> None:
    pdf.parent.mkdir(parents=True, exist_ok=True)
    if pdf.exists() and pdf.stat().st_mtime >= svg.stat().st_mtime:
        return
    cmd = [
        "inkscape",
        str(svg),
        f"--export-filename={pdf}",
        "--export-type=pdf",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        cmd = ["inkscape", str(svg), f"--export-pdf={pdf}"]
        result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(f"inkscape failed for {svg}")


def main() -> None:
    generate_script_figures()
    text = SCRIPT.read_text(encoding="utf-8")

    # pandoc-citeproc treats @fig:… as citations; use neutral phrasing instead.
    text = re.sub(r"@fig:[a-z0-9-]+", "die zugehörige Abbildung", text)
    text = re.sub(r"@tbl:[a-z0-9-]+", "die folgende Tabelle", text)

    for match in re.finditer(r"\.\./images/([a-zA-Z0-9_.-]+)\.svg", text):
        name = match.group(1)
        svg = resolve_svg(name)
        pdf = FIG_DIR / f"{name}.pdf"
        convert_svg(svg, pdf)
        text = text.replace(f"../images/{name}.svg", f"build/figures/{name}.pdf")

    BUILD_SCRIPT.write_text(text, encoding="utf-8")
    print(f"Wrote {BUILD_SCRIPT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
