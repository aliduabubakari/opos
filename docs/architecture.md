# OPOS Architecture

This document describes the OPOS standard architecture — the design rationale, the two-layer model, and the integration pattern that makes pipeline orchestration portable.

---

## 1. Design Rationale

### The Problem

Data pipelines are described in many ways: natural language, code comments, README files, architecture diagrams, YAML configs. To execute them, you need to translate those descriptions into orchestrator-specific DAGs (Airflow, Prefect, Dagster, Argo, etc.).

Without a standard, every description format must be mapped directly to every orchestrator:

```
Description A ──→ Airflow DAG
Description A ──→ Prefect Flow
Description A ──→ Dagster Job
Description B ──→ Airflow DAG
Description B ──→ Prefect Flow
Description B ──→ Dagster Job
...
```

This is an **N × M integration problem**: N description formats × M orchestrators = N×M mappings.

### The OPOS Solution

OPOS inserts a stable intermediate representation between description and execution:

```
Any Description ──→ PipeSpec ──→ OrchSpec ──→ Any Orchestrator
                      ↑            ↑
                 Extraction     Canonical
                   Layer          Layer
```

This reduces the problem from **N × M** to **N + M**:

- **N mappings** from description formats → PipeSpec (extraction)
- **1 deterministic compiler** from PipeSpec → OrchSpec
- **M mappings** from OrchSpec → orchestrator targets (projection)

Each mapping is built once and reused across all other integrations.

---

## 2. Layer Design

### 2.1 PipeSpec — The Extraction Layer

**Purpose:** Capture pipeline intent from natural language or code descriptions.

**Design principles:**
- **LLM-friendly**: Enums are descriptive strings ("Extractor", "python"), not numeric codes. Fields have human-readable names. Nulls are tolerated.
- **Flexible schema**: `additionalProperties: false` at the top level prevents drift, but within objects, free-form fields like `executor_config` and `authentication` allow variation.
- **Non-deterministic**: Two LLM runs on the same description will produce semantically equivalent but structurally different PipeSpec documents. This is accepted — determinism is the canonical layer's job.
- **Extraction-focused**: PipeSpec captures "what was understood" from a description, not "what will execute." Business logic payloads (Python scripts, SQL queries) are referenced, not embedded.

**Key schema sections:**
- `pipeline_summary` — name, description, flow patterns, complexity
- `components` — tasks with categories, executor types, I/O specs
- `flow_structure` — DAG topology with nodes and edges
- `parameters` — typed parameters and environment secrets
- `integrations` — external system connections and data lineage

### 2.2 OrchSpec — The Canonical Layer

**Purpose:** Provide a deterministic, validated, and projectable representation of a pipeline.

**Design principles:**
- **Deterministic**: Same PipeSpec input + same compiler version = byte-identical OrchSpec output. Achieved through canonical ordering (topological sort, lexicographic key sorting), ID canonicalization, type normalization, and null omission.
- **Strict schema**: Every field has a defined type, enum, and pattern. No free-form strings where enums apply.
- **Machine-validated**: Schema validation + 21 semantic rules (SEM001–SEM021) check structural integrity, reference integrity, graph connectivity, configuration coherence, resource integrity, and more.
- **Projectable**: Adapter plugins transform OrchSpec into target orchestrator DAGs. Real projections exist for Airflow, Prefect, Dagster, and Argo Workflows.

**Key schema sections:**
- `metadata` — pipeline identity, ownership, provenance
- `schedule` — cron-based scheduling
- `parameters` — typed parameters with normalized enums (STRING, INT, FLOAT, etc.)
- `secrets` — secret references with sensitivity levels
- `integrations` — external system catalogue with authentication
- `container_runtime` — default container configuration
- `components` — pipeline steps with normalized executor types
- `flow` — DAG topology with entry points, edges, parallelism groups
- `error_handling` — failure policies and notifications
- `observability` — logging, metrics, lineage
- `ots_export` — Open Transformation Standard mappings
- `provenance` — source file, generator, timestamps

### 2.3 Comparison

| Property | PipeSpec | OrchSpec |
|----------|----------|----------|
| **Version field** | `pipespec_version: "1.0"` | `orchspec_version: "1.0"` |
| **Pipeline name** | `pipeline_summary.name` (free-form) | `pipeline_id` (canonicalized) + `metadata.name` |
| **Executor types** | `python`, `http`, `docker`, `custom` | `python_script`, `http_request`, `container`, `custom` |
| **Parameter types** | lowercase: `string`, `integer`, `float` | UPPERCASE: `STRING`, `INT`, `FLOAT` |
| **Flow model** | `flow_structure.nodes` + `flow_structure.edges` | `components` are nodes + `flow.edges` |
| **I/O model** | `io_spec[]` with `direction` field | Separate `inputs[]` and `outputs[]` arrays |
| **Integrations** | `integrations.connections[]` with nested lineage | `integrations[]` flat array |
| **Determinism** | Not guaranteed | Guaranteed |
| **Validation** | Schema only | Schema + 21 semantic rules |

---

## 3. The Compiler Bridge

The `pipespec2orchspec` compiler is the critical bridge between layers. It performs:

### 3.1 Field Mapping

| PipeSpec | OrchSpec |
|----------|----------|
| `pipeline_summary.name` | `pipeline_id` + `metadata.name` |
| `pipeline_summary.description` | `description` |
| `pipeline_summary.complexity` | `metadata.complexity` |
| `flow_structure.pattern` | `flow.pattern` |
| `flow_structure.entry_points` | `flow.entry_points` |
| `flow_structure.edges` | `flow.edges` |
| `components[].executor_type` | `components[].executor.type` |
| `components[].io_spec` | `components[].inputs` + `components[].outputs` |

### 3.2 Normalization

- Executor types: `python` → `python_script`, `http` → `http_request`, `docker` → `container`
- Parameter types: `integer` → `INT`, `float` → `FLOAT`, `boolean` → `BOOLEAN`
- Integration types: `objectstore` → `object_store`, `queue` → `message_queue`
- IO formats: `TXT` → `text`
- Edge types: `conditional` → `success` (with condition preserved)
- Schedule expressions: `"manual"` → disabled schedule

### 3.3 Canonical Ordering

- Components are topologically sorted (Kahn's algorithm) with lexicographic tie-breaking
- Integrations are sorted by `id`
- All JSON keys are serialized in lexicographic order
- Edges are sorted by `(from, to)` tuple

### 3.4 Determinism Guarantee

Given identical PipeSpec input bytes and the same compiler version, the OrchSpec output is byte-identical. This enables:
- **Golden testing**: Compiler output is checked against committed snapshots
- **CI/CD diffing**: Pipeline changes produce deterministic, auditable diffs
- **Reproducibility**: Teams can independently verify compilation results

---

## 4. Projection Model

Once a pipeline is in OrchSpec canonical form, it can be projected onto any orchestrator through adapter plugins.

### 4.1 Adapter Protocol

Every adapter implements three methods:

```python
class OrchspecAdapter(Protocol):
    def capability(self) -> AdapterCapability: ...
    def validate_invariants(self, orchspec_doc: dict) -> list[str]: ...
    def project(self, orchspec_doc: dict) -> ProjectionResult: ...
```

### 4.2 Real Projections (v1.0)

| Target | Output Format | Features |
|--------|--------------|----------|
| **Airflow 2.x** | Python (TaskFlow API) | `@dag`, `@task`, 7 operator types, schedules, retries, timeouts |
| **Prefect 2.x** | Python (`@flow`/`@task`) | Retries, timeouts, `.serve()` deployments |
| **Dagster** | Python (`@asset`) | Asset dependencies, `RetryPolicy`, `ScheduleDefinition` |
| **Argo Workflows** | YAML (WorkflowTemplate) | DAG tasks, `CronWorkflow`, retry strategy, container scripts |

### 4.3 Stub Projections

Kestra, Kubeflow, and Flyte adapters emit placeholder IR — ready for real generators to be implemented.

---

## 5. Extensibility

Both layers are designed for extension:

### PipeSpec extensions
- Custom component categories via the `Custom` category
- Free-form `executor_config` for executor-specific parameters
- `extensions` field at both top-level and per-component for org-specific data

### OrchSpec extensions
- `executor.type: "custom"` with `custom_class` for non-standard executors
- `category: "Custom"` for domain-specific component types
- `integration.type: "custom"` for unlisted external systems
- `metadata.labels` and `metadata.tags` for arbitrary metadata
- JSON Schema `allOf` wrappers for domain-specific required fields
- Pluggable adapter framework for new orchestrator targets

---

## 6. Versioning

Each layer follows [Semantic Versioning](https://semver.org/) independently:

- **PipeSpec v1.0**: Stable extraction schema
- **OrchSpec v1.0**: Stable canonical schema with 21 validation rules
- **Compiler**: Versioned separately; pin for reproducibility

The OPOS standard itself is versioned through the combination of its layer versions. An OPOS-conformant implementation specifies which versions of PipeSpec and OrchSpec it supports.

---

## 7. Related Projects

| Project | Relationship |
|---------|-------------|
| [PipeSpec](https://github.com/aliduabubakari/pipespec) | Extraction layer — PipeSpec schema, validator, LLM generation tools |
| [OrchSpec](https://github.com/aliduabubakari/orchspec) | Canonical layer — OrchSpec schema, compiler, validator, diff, adapters |
| Apache Airflow | Target orchestrator (real projection) |
| Prefect | Target orchestrator (real projection) |
| Dagster | Target orchestrator (real projection) |
| Argo Workflows | Target orchestrator (real projection) |
| Kestra, Kubeflow, Flyte | Target orchestrators (stub projections) |
