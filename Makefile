# Top-level build targets for slides, figures, and lecture script PDF.
.PHONY: site slides figures figures-script script-pdf script-pdf-refresh refresh-data clean

site slides:
	npm run build:site

figures:
	$(PYTHON) scripts/generate_figures.py

figures-script:
	$(PYTHON) scripts/generate_figures.py --script

refresh-data:
	$(PYTHON) scripts/generate_figures.py --force
	$(PYTHON) scripts/generate_figures.py --script --force

script-pdf:
	$(MAKE) -C lecture pdf PREPARE_FLAGS=--offline

script-pdf-refresh:
	$(MAKE) -C lecture pdf PREPARE_FLAGS=--refresh-figures

clean:
	$(MAKE) -C lecture clean

PYTHON ?= python3
