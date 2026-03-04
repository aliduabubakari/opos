# OPOS

OPOS is a standalone standard for pipeline orchestration abstraction.

This repository publishes:
- OPOS v1.0 schema and specification
- Deterministic `pipespec2opos` compiler
- `opos-validate` schema+semantic validator
- `opos-diff` semantic comparator

## Install

```bash
pip install opos-validator
```

## CLI

```bash
pipespec2opos input.json --out output.yaml --format yaml --strict
opos-validate output.yaml --json-report
opos-diff old.yaml new.yaml --json-report
```

## Python API

```python
from opos_validator import CompileOptions, compile_pipespec_to_opos, validate_opos, semantic_diff_opos

opos = compile_pipespec_to_opos(pipespec_doc, options=CompileOptions(strict=True))
report = validate_opos(opos)
diff = semantic_diff_opos(opos_a, opos_b)
```

## Golden Regression Workflow

Check golden files:

```bash
PYTHONPATH=src python tools/golden.py --check
# or
make golden-check
```

Update golden files intentionally after mapping-rule changes:

```bash
PYTHONPATH=src python tools/golden.py --update-golden
# or
make update-golden
```

## Repository Layout

- `spec/` canonical schema and normative specification
- `docs/` field references and compiler rules
- `src/opos_validator/` package source
- `tests/` unit/integration and golden determinism tests
