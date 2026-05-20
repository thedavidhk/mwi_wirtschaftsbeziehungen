# Internationale Wirtschaftsbeziehungen

Lecture slides (reveal.js) and accompanying script (Pandoc/PDF) for the course *Internationale Wirtschaftsbeziehungen* at Hochschule Anhalt.

This repository is a **lecture project**. [reveal.js](https://revealjs.com/) is used as an npm dependency, not vendored as a fork.

## Quick start (slides)

Requirements: Node.js 18+

```bash
npm install
npm run build    # compile custom CSS + copy reveal.js into vendor/
npm start        # http://localhost:8000 — open index.html
```

Edit [`slides.md`](slides.md). Speaker notes use `Notes:` blocks (see reveal.js markdown docs).

**Note:** Slides with `data-external-html` need a local HTTP server (`npm start`), not `file://`.

## Figures and data

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/generate_figures.py
```

Caches live under `data/cache/`; SVGs are written to `images/`.

## Lecture script (PDF)

See [`lecture/README.md`](lecture/README.md) for the Pandoc/XeLaTeX workflow (`make pdf` in `lecture/`).

## Project layout

| Path | Purpose |
|------|---------|
| `slides.md` | Slide content (Markdown) |
| `index.html` | Deck shell and plugin config |
| `assets/` | Custom CSS and plugins |
| `vendor/reveal.js/` | Generated from `npm run build` (gitignored) |
| `images/` | Figures and photos |
| `lecture/` | Printable script (`script.md` → PDF) |

## Archived semesters (reveal.js fork layout)

Older semesters used an embedded reveal.js fork. They remain on these branches (tag: `archive/pre-restructure-2026`):

- `sose_24`
- `wise_2324`
- `sose_26` (last fork-era state before `main`)

New semesters should branch from `main`.

## License

Slide content: course materials. reveal.js: MIT (see [LICENSE](LICENSE)).
