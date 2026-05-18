# PDF aus dem Begleitscript erzeugen (Pandoc + pandoc-citeproc + XeLaTeX + Inkscape)
SCRIPT_SRC  := script.md
SCRIPT      := script.build.md
PDF         := script.pdf
META        := metadata.yaml
BIB         := references.bib
PREPARE     := prepare_build.py
FIG_SRC1    := ../images/capital_market1.html
FIG_OUT1    := ../images/capital_market1.svg
FIG_SRC2    := ../images/capital_market2.html
FIG_OUT2    := ../images/capital_market2.svg

PANDOC      ?= pandoc
PDF_ENGINE  ?= xelatex
PYTHON      ?= python3

.PHONY: all pdf figures prepare clean

all: pdf

figures:
	@test -f $(FIG_OUT1) || cp $(FIG_SRC1) $(FIG_OUT1)
	@test -f $(FIG_OUT2) || cp $(FIG_SRC2) $(FIG_OUT2)

prepare: figures $(SCRIPT)

$(SCRIPT): $(SCRIPT_SRC) $(PREPARE) $(BIB)
	$(PYTHON) $(PREPARE)

pdf: prepare $(PDF)

$(PDF): $(SCRIPT) $(META) $(BIB)
	$(PANDOC) $(SCRIPT) $(META) -o $(PDF) \
	  --resource-path=.:.. \
	  --bibliography=$(BIB) \
	  --filter pandoc-citeproc \
	  --pdf-engine=$(PDF_ENGINE)

clean:
	rm -f $(PDF) $(SCRIPT)
	rm -rf build
