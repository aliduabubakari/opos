# OPOS

OPOS is a standalone standard for pipeline orchestration abstraction.

This repository publishes:
- OPOS v1.0 schema and specification
- Deterministic `pipespec2opos` compiler
- `opos-validate` schema+semantic validator
- `opos-diff` semantic comparator
- Adapter interfaces/stubs for future multi-orchestrator projection

## Install

```bash
pip install opos-validator
```

## CLI

```bash
pipespec2opos input.json --out output.yaml --format yaml --strict
opos-validate output.yaml --json-report
opos-validate output.yaml --strict
opos-diff old.yaml new.yaml --json-report
```

## Python API

```python
from opos_validator import CompileOptions, compile_pipespec_to_opos, validate_opos, semantic_diff_opos

opos = compile_pipespec_to_opos(pipespec_doc, options=CompileOptions(strict=True))
report = validate_opos(opos, strict=True)
diff = semantic_diff_opos(opos_a, opos_b)
```

## Compiler Contracts

- Strict PipeSpec profile: `spec/pipespec_profile_v1.json`
- Formal mapping spec: `spec/mappings/pipespec_to_opos_v1.json`

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

- `spec/` canonical schema, profile, and mapping specs
- `docs/` field references and compiler rules
- `src/opos_validator/` package source
- `tests/` unit/integration and golden determinism tests
- `samples/pipespecs/` short corpus for valid/invalid scenario testing
