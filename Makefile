PYTHONPATH ?= src

.PHONY: test golden-check update-golden

test:
	PYTHONPATH=$(PYTHONPATH) pytest -q

golden-check:
	PYTHONPATH=$(PYTHONPATH) python tools/golden.py --check

update-golden:
	PYTHONPATH=$(PYTHONPATH) python tools/golden.py --update-golden
