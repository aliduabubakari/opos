# OPOS Changelog

All notable changes to the OPOS standard.

---

## 1.0.0 — 2026-06-25

### Standard Definition

- **Two-layer architecture defined**: PipeSpec (extraction layer) + OrchSpec (canonical layer)
- **Conformance specification** (`spec/opos-overview.md`): three implementation profiles (Full OPOS, OrchSpec-Only, PipeSpec-Only)
- **Architecture document** (`docs/architecture.md`): design rationale, layer comparison, compiler bridge, projection model, extensibility patterns

### PipeSpec v1.0 (Extraction Layer)

- LLM-friendly pipeline extraction format
- JSON Schema v1.0 (`pipespec_schema_v1.json`)
- Component taxonomy: Extractor, Transformer, Loader, Reconciliator, QualityCheck, Notifier, Sensor, Custom
- Flow patterns: sequential, parallel, dag, conditional, loop
- 7 executor types: python, http, sql, bash, email, docker, custom
- Typed parameters with environment/secret references
- Integration catalogue with data lineage
- Python CLI: `pipespec validate`, `pipespec generate`, `pipespec diff`

### OrchSpec v1.0 (Canonical Layer)

- Deterministic PipeSpec → OrchSpec compiler (`pipespec2orchspec`)
- JSON Schema v1.0 (`orchspec_schema_v1.json`)
- 21 semantic validation rules (SEM001–SEM021)
- Schema + semantic validator (`orchspec-validate`)
- Semantic diff engine (`orchspec-diff`)
- Adapter framework with OrchSpecAdapter Protocol
- **Real projections**: Airflow 2.x (TaskFlow API), Prefect 2.x, Dagster, Argo Workflows
- **Stub projections**: Kestra, Kubeflow Pipelines, Flyte
- 112 tests covering all compiler error codes, validation rules, edge cases, and adapters
- Formal specification (`orchspec-spec-v1.md`): execution semantics, determinism guarantees, extensibility patterns

### Meta-Project

- OPOS as the umbrella standard linking both layers
- Reduced integration complexity from N×M to N+M
- Cross-repository architecture: `opos` (standard), `pipespec` (extraction), `orchspec` (canonical)
- Contribution guides for all three repositories
