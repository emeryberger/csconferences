PYTHON = python3

all:
	$(PYTHON) build.py --sort
	$(PYTHON) build.py --all > README.md
	@if [ -f index.html ]; then $(MAKE) --no-print-directory explorer-home; fi

# Make the interactive explorer the site homepage (csconferences.org/).
# Generates a root index.html that loads explore/ via <base href>, so explore/ stays the
# single source of truth. GitHub Pages serves index.html in preference to README.md.
# Undo with: make readme-home
explorer-home:
	sed -e 's#<head>#<head><base href="explore/">#' \
	    -e 's#<a href="\.\./" data-static>#<a href="https://github.com/emeryberger/csconferences\#readme" data-static>#' \
	    explore/index.html > index.html

readme-home:
	rm -f index.html

.PHONY: explorer-home readme-home
