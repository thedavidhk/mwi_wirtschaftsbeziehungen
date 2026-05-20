# Internationale Wirtschaftsbeziehungen

Lecture slides (reveal.js) and accompanying script (Pandoc/PDF) for the course *Internationale Wirtschaftsbeziehungen* at Hochschule Anhalt.

This repository is a **lecture project**. [reveal.js](https://revealjs.com/) is used as an npm dependency, not vendored as a fork.

## Quick start (slides)

Requirements: Node.js 18+

```bash
npm install
npm run build    # compile custom CSS + copy reveal.js into assets/reveal/
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
| `assets/reveal/` | Generated from `npm run build` (gitignored; published via `gh-pages` branch) |
| `images/` | Figures and photos |
| `lecture/` | Printable script (`script.md` → PDF) |

## Archived semesters (reveal.js fork layout)

Older semesters used an embedded reveal.js fork. They remain on these branches (tag: `archive/pre-restructure-2026`):

- `sose_24`
- `wise_2324`
- `sose_26` (last fork-era state before `main`)

New semesters should branch from `main`.

## GitHub Pages

Slides are deployed via [`.github/workflows/pages.yml`](.github/workflows/pages.yml): each push to `main` builds `site/` and pushes it to the **`gh-pages`** branch.

**One-time setup** (repo Settings on GitHub):

1. **Settings → Pages → Build and deployment → Source:** **Deploy from a branch**
2. **Branch:** **`gh-pages`** · **Folder:** **`/ (root)`**
3. **Settings → General → Default branch:** **`main`** (lecture sources; `gh-pages` is generated only by CI)

Do **not** point Pages at `main` — that branch has no built `assets/reveal/` or `custom.css` (they are generated in CI).

**After each push to `main`**, wait for the **deploy-pages** workflow, then open:

`https://thedavidhk.github.io/mwi_wirtschaftsbeziehungen/`

Local check before pushing:

```bash
npm run build:site
npx --yes serve site -l 8000
```

`index.html` sets a `<base href="/<repo>/">` on `*.github.io` so asset paths work on project Pages.

## License

Slide content: course materials. reveal.js: MIT (see [LICENSE](LICENSE)).
