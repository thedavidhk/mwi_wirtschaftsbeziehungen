# Internationale Wirtschaftsbeziehungen

Lecture slides (reveal.js) and accompanying script (Pandoc/PDF) for the course *Internationale Wirtschaftsbeziehungen* at Hochschule Anhalt.

This repository is a **lecture project**. [reveal.js](https://revealjs.com/) is used as an npm dependency, not vendored as a fork.

## Build environment (Nix)

```bash
nix develop   # Node, Python (matplotlib/pandas/… from nixpkgs), pandoc, XeLaTeX, rsvg-convert
make site     # GitHub Pages artifact in site/
make script-pdf
```

Without Nix: Node.js 18+, Python 3.11–3.12, `pip install -r requirements.txt`, plus pandoc, XeLaTeX, and `rsvg-convert` (librsvg). The Nix shell does **not** use a pip `.venv` (avoids broken wheels on Python 3.13 in CI).

## Quick start (slides)

```bash
npm install
npm run build    # compile custom CSS + copy reveal.js into assets/reveal/
npm start        # http://localhost:8000 — open index.html
```

Edit [`slides.md`](slides.md). Speaker notes use `Notes:` blocks (see reveal.js markdown docs).

**Note:** Slides with `data-external-html` need a local HTTP server (`npm start`), not `file://`.

## Figures and data

Committed **`images/`** and **`data/cache/`** are the source of truth for builds. External APIs are only called when you explicitly refresh data.

```bash
make figures              # slide SVGs → images/ (uses cache when fresh)
make refresh-data         # --force: re-download caches, regenerate all figures
```

Caches live under `data/cache/`; SVGs are written to `images/`.

**Static diagrams:** `capital_market1` / `capital_market2` are still Inkscape SVGs (slides embed the matching `.html` files). All other plot figures are produced by [`scripts/generate_figures.py`](scripts/generate_figures.py).

## Lecture script (PDF)

See [`lecture/README.md`](lecture/README.md). Summary:

```bash
make script-pdf           # offline from cache (CI uses this)
make script-pdf-refresh   # allow API/cache refresh while building
```

## Make targets

| Target | Purpose |
|--------|---------|
| `make site` | Build static site for GitHub Pages |
| `make figures` | Regenerate slide figures |
| `make refresh-data` | Force-refresh caches and figures |
| `make script-pdf` | Lecture script PDF (offline) |

## Project layout

| Path | Purpose |
|------|---------|
| `slides.md` | Slide content (Markdown) |
| `index.html` | Deck shell and plugin config |
| `assets/` | Custom CSS and plugins |
| `assets/reveal/` | Generated from `npm run build` (gitignored; published via `gh-pages` branch) |
| `images/` | Figures and photos |
| `data/cache/` | Pinned API responses for figure generation |
| `lecture/` | Printable script (`script.md` → PDF) |
| `flake.nix` | Reproducible dev shell |

## Archived semesters (reveal.js fork layout)

Older semesters used an embedded reveal.js fork. They remain on these branches (tag: `archive/pre-restructure-2026`):

- `sose_24`
- `wise_2324`
- `sose_26` (last fork-era state before `main`)

New semesters should branch from `main`.

## GitHub Pages

Slides are deployed via [`.github/workflows/pages.yml`](.github/workflows/pages.yml): each push to `main` builds `site/` and pushes it to the **`gh-pages`** branch.

The [`build`](.github/workflows/build.yml) workflow also builds `lecture/script.pdf` offline and uploads it as a CI artifact.

**One-time setup** (repo Settings on GitHub):

1. **Settings → Pages → Build and deployment → Source:** **Deploy from a branch**
2. **Branch:** **`gh-pages`** · **Folder:** **`/ (root)`**
3. **Settings → General → Default branch:** **`main`** (lecture sources; `gh-pages` is generated only by CI)

Do **not** point Pages at `main` — that branch has no built `assets/reveal/` or `custom.css` (they are generated in CI).

**After each push to `main`**, wait for the **deploy-pages** workflow, then open:

`https://thedavidhk.github.io/mwi_wirtschaftsbeziehungen/`

Local check before pushing:

```bash
make site
npx --yes serve site -l 8000
```

`index.html` sets a `<base href="/<repo>/">` on `*.github.io` so asset paths work on project Pages.

## License

Slide content: course materials. reveal.js: MIT (see [LICENSE](LICENSE)).
