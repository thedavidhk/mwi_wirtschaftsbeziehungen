# Begleitscript (Markdown → PDF)

Textbuchartiges Vorlesungsscript zu den Folien in `slides.md`: Fließtext, Abbildungen aus `images/`, Literatur in **BibTeX** (`references.bib`).

## Dateien

| Datei | Zweck |
|--------|--------|
| `script.md` | Inhalt (Quelle, von Ihnen gepflegt) |
| `references.bib` | Literatur und Datenquellen |
| `metadata.yaml` | Pandoc/LaTeX (Layout, Sprache, Inhaltsverzeichnis) |
| `prepare_build.py` | SVG→PDF (Inkscape), erzeugt `script.build.md` |
| `Makefile` | Build-Orchestrierung |

## PDF erzeugen

Voraussetzungen: `pandoc`, `pandoc-citeproc`, `xelatex` (TeX Live), `inkscape`, `python3`.

```bash
cd lecture
make pdf
```

Ergebnis: `lecture/script.pdf` (nicht versioniert; `make clean` entfernt Build-Artefakte).

### Ablauf

1. `prepare_build.py` wandelt eingebundene SVGs nach `build/figures/*.pdf` und schreibt `script.build.md`.
2. Pandoc + `pandoc-citeproc` erzeugen das PDF mit Literaturverzeichnis.

### HTML (ohne LaTeX)

```bash
python3 prepare_build.py
pandoc script.build.md -o script.html \
  --metadata-file=metadata.yaml \
  --resource-path=.:.. --bibliography=references.bib \
  --filter pandoc-citeproc --standalone
```

## Pflege

1. Folien geändert → passende Abschnitte in `script.md` anpassen.
2. Neue Grafik → in `script.md` per `![](../images/….svg)` einbinden; `make pdf` konvertiert automatisch.
3. Neue Quelle → Eintrag in `references.bib`, im Text `[@schlüssel]`.
4. Abbildungsverweise in `script.md` als `@fig:…` (an die `{#fig:…}`-Labels der Bilder angelehnt). `prepare_build.py` wandelt sie für das PDF in LaTeX-Querverweise (`\autoref{fig:…}`) um, damit citeproc sie nicht als Zitate liest.

Abbildungsdaten stammen dieselben Caches wie die Folien (`data/cache/`), wenn Sie `scripts/generate_figures.py` ausführen.

## Bibliographie

**BibTeX** (`.bib`) — Standard für Pandoc/LaTeX und Referenzmanager (Zotero, JabRef). Mix aus Lehrbüchern, Working Papers, Datenbanken (`@misc`) und Presse (`@article` mit URL) für aktuelle Themen.
