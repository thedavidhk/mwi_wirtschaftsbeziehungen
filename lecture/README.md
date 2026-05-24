# Begleitscript (Markdown → PDF)

Textbuchartiges Vorlesungsscript zu den Folien in `slides.md`: Fließtext, Abbildungen aus `images/`, Literatur in **BibTeX** (`references.bib`).

## Dateien

| Datei | Zweck |
|--------|--------|
| `script.md` | Inhalt (Quelle, von Ihnen gepflegt) |
| `references.bib` | Literatur und Datenquellen |
| `metadata.yaml` | Pandoc/LaTeX (Layout, Sprache, Inhaltsverzeichnis) |
| `prepare_build.py` | SVG→PDF (`rsvg-convert`), erzeugt `script.build.md` |
| `Makefile` | Build-Orchestrierung |

## PDF erzeugen

Voraussetzungen: `pandoc`, `pandoc-citeproc`, `xelatex` (TeX Live), `rsvg-convert` (librsvg), `python3`.

Empfohlen: `nix develop` im Repo-Root (siehe `flake.nix`), dann:

```bash
make script-pdf          # offline: cache + committed images only
# oder
make script-pdf-refresh    # lädt fehlende/veraltete Cache-Dateien nach
```

Alternativ nur in `lecture/`:

```bash
cd lecture
make pdf                 # offline (Standard)
make pdf PREPARE_FLAGS=--refresh-figures
```

Ergebnis: `lecture/script.pdf` (nicht versioniert; `make clean` entfernt Build-Artefakte).

### Ablauf

1. `prepare_build.py` baut matplotlib-Abbildungen für den Druck (`generate_figures.py --script --offline` standardmäßig), wandelt SVGs nach `build/figures/*.pdf`, schreibt `script.build.md`.
2. Statische Diagramme (`capital_market1.svg`, `capital_market2.svg`) werden für helles Papier angepasst (kein API-Aufruf).
3. Pandoc + `pandoc-citeproc` erzeugen das PDF mit Literaturverzeichnis.

### HTML (ohne LaTeX)

```bash
python3 prepare_build.py --offline
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

Datenaktualisierung (jährlich o. ä.): im Repo-Root `make refresh-data`, dann `images/` und `data/cache/` prüfen und committen.

## Bibliographie

**BibTeX** (`.bib`) — Standard für Pandoc/LaTeX und Referenzmanager (Zotero, JabRef). Mix aus Lehrbüchern, Working Papers, Datenbanken (`@misc`) und Presse (`@article` mit URL) für aktuelle Themen.
