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

### The Full Pipeline Stack

OPOS addresses the **orchestration layer** — what components exist, how they connect, and how they're scheduled. But a complete pipeline also needs a **transformation layer** — what actually runs inside each component.

OPOS references the [Open Transformation Specification (OTS)](https://github.com/francescomucio/open-transformation-specification) as the complementary standard for the transformation layer. Together they cover the full stack:

```
┌─────────────────────────────────────────────────────────┐
│                    Full Pipeline Stack                   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              OPOS (Orchestration)                 │    │
│  │                                                   │    │
│  │  PipeSpec ──→ OrchSpec ──→ Airflow/Prefect/...   │    │
│  │  (describe)    (define)     (execute)             │    │
│  │                         │                         │    │
│  │                         │ ots_export              │    │
│  │                         ▼                         │    │
│  │  ┌─────────────────────────────────────────┐     │    │
│  │  │          OTS (Transformation)            │     │    │
│  │  │                                         │     │    │
│  │  │  SQL queries, materialization,          │     │    │
│  │  │  data quality tests, UDFs               │     │    │
│  │  │                                         │     │    │
│  │  │  github.com/francescomucio/             │     │    │
│  │  │    open-transformation-specification    │     │    │
│  │  └─────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

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

## 5. The Transformation Layer — OTS

While OPOS defines the **orchestration layer** (what runs, in what order, on what schedule), the [Open Transformation Specification (OTS)](https://github.com/francescomucio/open-transformation-specification) defines the **transformation layer** (what SQL or code executes inside each component).

### 5.1 What OTS Is

OTS is a community-driven open specification (currently v0.2.1) that standardizes how data transformations are defined. It covers:

| Artifact | Description |
|----------|-------------|
| **Open Transformation Definition (OTD)** | A structured definition of a SQL data transformation, including source tables, target materialization, and business logic |
| **UDF Definition** | A user-defined function with signature, implementation, and dependencies |
| **Test Definition** | A data quality test with SQL assertions, parameters, and scope (table or column level) |
| **OTS Module** | A collection of related transformations, UDFs, and tests targeting the same database and schema |

OTS is to data transformations what OrchSpec is to orchestration: a portable, tool-agnostic specification that enables interoperability.

### 5.2 The Bridge: `ots_export`

OrchSpec's schema includes an `ots_export` field that maps orchestration components to transformation definitions:

```json
{
  "ots_export": {
    "ots_version": "0.2.1",
    "module_id": "sales_analytics",
    "component_mappings": [
      {
        "component_id": "transform_sales",
        "ots_type": "sql_transformation",
        "ots_transformation_id": "daily_sales_agg",
        "materialization": "incremental"
      },
      {
        "component_id": "validate_quality",
        "ots_type": "sql_transformation",
        "ots_transformation_id": "sales_quality_checks",
        "materialization": "ephemeral"
      }
    ]
  }
}
```

This bridge means:
- An OrchSpec document declares **which components** exist and **how they connect** (orchestration)
- An OTS document declares **what transformation** each component executes (transformation)
- The `ots_export` field links them, mapping component IDs to OTS transformation IDs with materialization strategies

### 5.3 Why Separate Specifications?

| Concern | OPOS (OrchSpec) | OTS |
|---------|----------------|-----|
| **Layer** | Orchestration | Transformation |
| **Question answered** | "What runs, in what order, on what schedule?" | "What SQL/transformation runs inside each step?" |
| **Audience** | Platform engineers, CI/CD, orchestrator operators | Analytics engineers, data engineers, SQL developers |
| **Lifecycle** | DAG deployment, scheduling, monitoring | Transformation development, testing, materialization |
| **Tools** | Airflow, Prefect, Dagster, Argo | dbt, SQLMesh, Tee for Transform, OTS-compliant tools |
| **Versioning** | Independently versioned (v1.0) | Independently versioned (v0.2.1) |

Keeping them separate is intentional:
- Each spec can evolve at its own pace
- Each spec serves its own community
- Implementations can choose which layers to adopt
- The bridge (`ots_export`) keeps them connected without coupling

### 5.4 Analogy: OpenAPI + JSON Schema

The OPOS/OTS relationship mirrors OpenAPI and JSON Schema:
- **OpenAPI** defines the API structure (endpoints, methods, parameters) — like OrchSpec defines the DAG structure
- **JSON Schema** defines the data shape (types, validation, constraints) — like OTS defines the transformation shape
- OpenAPI **references** JSON Schema; it doesn't embed or replace it
The same principle applies here: OrchSpec references OTS for transformation definitions.

---

## 6. Extensibility

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

## 7. Versioning

Each layer follows [Semantic Versioning](https://semver.org/) independently:

- **PipeSpec v1.0**: Stable extraction schema
- **OrchSpec v1.0**: Stable canonical schema with 21 validation rules
- **OTS**: Independently versioned by its community (currently v0.2.1)
- **Compiler**: Versioned separately; pin for reproducibility

The OPOS standard itself is versioned through the combination of its layer versions. An OPOS-conformant implementation specifies which versions of PipeSpec and OrchSpec it supports.

---

## 8. Related Projects

| Project | Relationship |
|---------|-------------|
| [PipeSpec](https://github.com/aliduabubakari/pipespec) | Extraction layer — PipeSpec schema, validator, LLM generation tools |
| [OrchSpec](https://github.com/aliduabubakari/orchspec) | Canonical layer — OrchSpec schema, compiler, validator, diff, adapters |
| [OTS](https://github.com/francescomucio/open-transformation-specification) | Transformation layer — SQL transformations, data quality tests, UDFs; referenced by OrchSpec's `ots_export` field |
| Apache Airflow | Target orchestrator (real projection) |
| Prefect | Target orchestrator (real projection) |
| Dagster | Target orchestrator (real projection) |
| Argo Workflows | Target orchestrator (real projection) |
| Kestra, Kubeflow, Flyte | Target orchestrators (stub projections) |
| dbt, SQLMesh, Tee for Transform | Transformation tools compatible with OTS |

---

## 9. Future Evolution

### 9.1 OTS Adapter

A natural next step is an **OTS adapter** for OrchSpec that reads the `ots_export` field and generates OTS-compliant transformation definitions alongside the orchestrator DAG. This would enable:

```
PipeSpec ──→ OrchSpec ──┬──→ Airflow DAG (orchestration)
                         └──→ OTS Module (transformation)
```

A single OrchSpec document would project to both layers simultaneously — the orchestrator DAG for scheduling and execution, and the OTS module for transformation definition and materialization.

### 9.2 Remaining Stub Adapters

Real projectors for Kestra (declarative YAML flows), Kubeflow Pipelines (Python SDK), and Flyte (Flytekit) would bring the adapter count to 7 real projections.

### 9.3 Bidirectional Compilation

An OrchSpec → PipeSpec reverse compiler would enable roundtrip validation: compile PipeSpec → OrchSpec → PipeSpec' and verify semantic equivalence.

### 9.4 Visualization & Tooling

- DAG graph visualization from OrchSpec documents
- Schema registry for OPOS-compatible extensions
- CI/CD integration for pipeline change auditing via `orchspec-diff`
