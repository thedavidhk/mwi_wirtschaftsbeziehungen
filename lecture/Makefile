# PDF aus dem Begleitscript erzeugen (Pandoc --citeproc + XeLaTeX + rsvg-convert)
SCRIPT_SRC  := script.md
SCRIPT      := script.build.md
PDF         := script.pdf
TEX         := build/script.tex
META        := metadata.yaml
BIB         := references.bib
PREPARE     := prepare_build.py

PANDOC      ?= pandoc
PDF_ENGINE  ?= xelatex
PYTHON      ?= python3

# Default: offline figure regen from data/cache/ (no API calls).
PREPARE_FLAGS ?=

.PHONY: all pdf prepare clean

all: pdf

prepare: $(SCRIPT)

$(SCRIPT): $(SCRIPT_SRC) $(PREPARE) $(BIB)
	$(PYTHON) $(PREPARE) $(PREPARE_FLAGS)

pdf: prepare $(PDF)

$(TEX): $(SCRIPT) $(META) $(BIB)
	$(PANDOC) $(SCRIPT) -o $(TEX) --standalone \
	  --metadata-file=$(META) \
	  --resource-path=.:.. \
	  --bibliography=$(BIB) \
	  --citeproc
	$(PYTHON) $(PREPARE) --fix-tex $(TEX)

$(PDF): $(TEX)
	latexmk -$(PDF_ENGINE) -interaction=nonstopmode -output-directory=build $(TEX)
	@test -f build/script.pdf && mv build/script.pdf $(PDF)
	@latexmk -c -output-directory=build $(TEX) 2>/dev/null || true

clean:
	rm -f $(PDF) $(SCRIPT)
	rm -rf build
