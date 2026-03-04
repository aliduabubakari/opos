# Compiler Guide

This guide defines deterministic PipeSpec v1.0 to OPOS v1.0 mapping.

## Canonical Ordering
- Sort `integrations` by `id`.
- Sort `components` by topological order from `flow.edges`, tie-break with `id`.
- Sort serialized object keys.

## Field Mapping
- `pipeline_summary.name` -> `metadata.name`
- `pipeline_summary.description` -> `description`
- `pipeline_summary.complexity` -> `metadata.complexity`
- `flow_structure.pattern` -> `flow.pattern`
- `flow_structure.entry_points` -> `flow.entry_points`
- `flow_structure.edges` -> `flow.edges`

Executor mapping:
- `python` -> `python_script`
- `http` -> `http_request`
- `sql` -> `sql`
- `bash` -> `bash`
- `container` -> `container`
- `email` -> `email`
- unknown -> `custom` (error in `--strict`)

## Normalization
- Parameter types are normalized to OPOS enums (`float` -> `FLOAT`, etc).
- Null/empty values are omitted from output unless required.
- Retry policy maps to OPOS `retry` with deterministic defaults.

## Unsupported Input Policy
- Strict mode (`--strict`) raises compile errors with stable IDs.
- Non-strict mode coerces unknown executor types to `custom`.
