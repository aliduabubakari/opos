# OPOS Field Reference

See canonical schema: `spec/opos_schema_v1.json`.

Key required top-level fields:
- `opos_version`
- `pipeline_id`
- `description`
- `metadata`
- `components`
- `flow`

Semantic validation is enforced by `opos-validate` with `SEM001..SEM010` rules.
