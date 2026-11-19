PYTHON = python3

all:
	$(PYTHON) build.py --sort
	$(PYTHON) build.py --all > README.md
	mkdir -p static && cp README.md static/index.md   # static page at /static/ (README.md is not rendered once index.html exists)
	@if [ -f index.html ]; then $(MAKE) --no-print-directory explorer-home; fi

# Make the interactive explorer the site homepage (csconferences.org/).
# Generates a root index.html that loads explore/ via <base href>, so explore/ stays the
# single source of truth. GitHub Pages serves index.html in preference to README.md.
# Undo with: make readme-home
explorer-home:
	sed -e 's#<head>#<head><base href="explore/">#' \
	    explore/index.html > index.html

readme-home:
	rm -f index.html

.PHONY: explorer-home readme-home
