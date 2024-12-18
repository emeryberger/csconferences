PYTHON = python3

all:
	$(PYTHON) build.py --sort
	$(PYTHON) build.py --all > README.md
