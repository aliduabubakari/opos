# OPOS v1.0 — LLM Skills Reference

> **A self-contained guide for LLMs to understand and work with the OPOS standard.**
>
> OPOS (Open Pipeline Orchestration Specification) defines two specification layers:
> **PipeSpec** (extraction format) and **OrchSpec** (canonical intermediate representation).
>
> Use this reference to understand the OPOS architecture, generate valid PipeSpec documents,
> reason about OrchSpec compilation, and understand the projection model.

---

## 1. What OPOS Is

OPOS is an open standard for describing, compiling, and projecting data pipelines. It separates pipeline orchestration into two layers:

```
Natural Language → PipeSpec → OrchSpec → Target Orchestrator
                   (extract)   (compile)   (project)
```

### Why Two Layers?

| Concern | PipeSpec | OrchSpec |
|---------|----------|----------|
| **Audience** | LLMs, humans | Machines, CI/CD |
| **Schema** | Flexible, tolerates variation | Strict, deterministic |
| **Determinism** | Not guaranteed | Byte-identical output guaranteed |
| **Validation** | Schema only | Schema + 21 semantic rules |
| **Output** | Human-readable description | Projectable IR for orchestrators |

### The Integration Model

Without OPOS: N source formats × M orchestrators = N×M mappings.
With OPOS: N + M mappings through a stable canonical intermediate representation.

---

## 2. PipeSpec v1.0 — Extraction Layer

PipeSpec captures pipeline intent in an LLM-friendly format. It describes **what** a pipeline does without embedding business logic payloads.

### 2.1 Top-Level Structure

```json
{
  "pipespec_version": "1.0",
  "metadata": { ... },
  "pipeline_summary": { ... },
  "components": [ ... ],
  "flow_structure": { ... },
  "parameters": { ... },
  "integrations": { ... }
}
```

### 2.2 Pipeline Summary

```json
{
  "pipeline_summary": {
    "name": "Daily ETL Pipeline",
    "description": "Extract from API, transform metrics, load to warehouse",
    "flow_patterns": ["sequential", "dag"],
    "task_executors": ["python", "sql", "http"],
    "complexity": "medium"
  }
}
```

**Complexity levels:** `low`, `medium`, `high`

### 2.3 Components

Each component is a pipeline step. Required fields: `id`, `name`, `category`, `executor_type`, `io_spec`.

```json
{
  "id": "extract_sales",
  "name": "Extract Sales Data",
  "category": "Extractor",
  "description": "Fetch daily sales from CRM API",
  "executor_type": "http",
  "io_spec": [
    {
      "name": "sales_data",
      "direction": "output",
      "kind": "api",
      "format": "json"
    }
  ],
  "retry_policy": {
    "max_attempts": 3,
    "delay_seconds": 60,
    "exponential_backoff": true,
    "retry_on": ["timeout", "server_error"]
  },
  "upstream_policy": {
    "type": "all_success"
  }
}
```

**Component categories:**

| Category | Typical Role |
|----------|-------------|
| `Extractor` | Ingest data from external sources |
| `Transformer` | Process, clean, enrich data |
| `Loader` | Write data to destinations |
| `Reconciliator` | Validate, reconcile, repair data |
| `QualityCheck` | Data quality gates and assertions |
| `Notifier` | Send alerts, emails, webhooks |
| `Sensor` | Wait for external conditions |
| `Custom` | Domain-specific pipeline steps |

**Executor types:**

| Type | Description |
|------|-------------|
| `python` | Python script or callable |
| `http` | HTTP API request |
| `sql` | SQL query or transformation |
| `bash` | Shell script |
| `email` | Email notification |
| `docker` | Container execution |
| `custom` | Extension point |

**I/O kinds:** `file`, `table`, `api`, `object`, `stream`

**I/O formats:** `json`, `csv`, `parquet`, `avro`, `html`, `sql`, `text`, `binary`

### 2.4 Flow Structure

```json
{
  "flow_structure": {
    "pattern": "dag",
    "entry_points": ["extract_sales"],
    "nodes": {
      "extract_sales": {
        "kind": "Task",
        "component_type_id": "extract_sales",
        "upstream_policy": { "type": "all_success" },
        "next_nodes": ["transform_metrics"]
      },
      "transform_metrics": {
        "kind": "Task",
        "component_type_id": "transform_metrics",
        "upstream_policy": { "type": "all_success" },
        "next_nodes": ["load_warehouse"]
      }
    },
    "edges": [
      { "from": "extract_sales", "to": "transform_metrics", "edge_type": "success" },
      { "from": "transform_metrics", "to": "load_warehouse", "edge_type": "success" }
    ]
  }
}
```

**Flow patterns:** `sequential`, `parallel`, `dag`, `conditional`, `loop`

**Edge types:** `success`, `failure`, `always`, `conditional`

### 2.5 Parameters

```json
{
  "parameters": {
    "pipeline": {
      "batch_size": {
        "description": "Number of records per batch",
        "type": "integer",
        "default": 1000,
        "required": false
      }
    },
    "schedule": {
      "expression": {
        "description": "Cron expression",
        "type": "string",
        "default": "0 6 * * *",
        "required": false
      }
    },
    "execution": {},
    "components": {},
    "environment": {
      "API_KEY": {
        "description": "CRM API key",
        "type": "string",
        "default": null,
        "required": true
      }
    }
  }
}
```

### 2.6 Integrations

```json
{
  "integrations": {
    "connections": [
      {
        "id": "crm_api",
        "name": "CRM API",
        "type": "api",
        "config": { "base_url": "https://api.crm.example.com" },
        "authentication": { "type": "bearer", "token_env_var": "API_KEY" },
        "used_by_components": ["extract_sales"],
        "direction": "input"
      }
    ],
    "data_lineage": {
      "sources": ["CRM API"],
      "sinks": ["Data Warehouse"],
      "intermediate_datasets": ["transformed_metrics"]
    }
  }
}
```

---

## 3. OrchSpec v1.0 — Canonical Layer

OrchSpec is the deterministic compilation target. PipeSpec is compiled into OrchSpec, which is then projected onto target orchestrators.

### 3.1 Top-Level Structure

```json
{
  "orchspec_version": "1.0",
  "pipeline_id": "daily_etl_pipeline",
  "description": "Extract from API, transform metrics, load to warehouse",
  "metadata": { ... },
  "schedule": { ... },
  "parameters": { ... },
  "secrets": [ ... ],
  "integrations": [ ... ],
  "components": [ ... ],
  "flow": { ... },
  "error_handling": { ... },
  "observability": { ... },
  "provenance": { ... }
}
```

### 3.2 Key Differences from PipeSpec

| Aspect | PipeSpec | OrchSpec |
|--------|----------|----------|
| Version field | `pipespec_version` | `orchspec_version` |
| Pipeline name | `pipeline_summary.name` | `pipeline_id` + `metadata.name` |
| Executor types | `python`, `http`, `docker` | `python_script`, `http_request`, `container` |
| Parameter types | `string`, `integer` | `STRING`, `INT` |
| Flow model | `flow_structure.nodes` map | Components ARE the nodes |
| I/O model | `io_spec[]` with direction | Separate `inputs[]` + `outputs[]` |
| Integrations | `integrations.connections[]` | `integrations[]` flat array |

### 3.3 Components in OrchSpec

```json
{
  "id": "extract_sales",
  "name": "Extract Sales Data",
  "category": "Extractor",
  "executor": { "type": "http_request", "http_method": "GET" },
  "inputs": [],
  "outputs": [
    { "name": "sales_data", "kind": "api", "format": "json" }
  ],
  "retry": {
    "max_attempts": 3,
    "delay_seconds": 60,
    "strategy": "exponential"
  },
  "timeout": "PT300S",
  "upstream_policy": "all_success"
}
```

**OrchSpec executor types:** `python_script`, `http_request`, `sql`, `email`, `bash`, `container`, `custom`

**Retry strategies:** `constant`, `exponential`, `random`

### 3.4 Flow in OrchSpec

```json
{
  "flow": {
    "pattern": "dag",
    "entry_points": ["extract_sales"],
    "edges": [
      { "from": "extract_sales", "to": "transform_metrics", "edge_type": "success" },
      { "from": "transform_metrics", "to": "load_warehouse", "edge_type": "success" }
    ]
  }
}
```

Components are topologically sorted. Edges can include `condition` expressions for conditional branching.

### 3.5 Schedule

```json
{
  "schedule": {
    "enabled": true,
    "cron": "0 6 * * *",
    "timezone": "America/New_York",
    "catchup": false,
    "start_date": "2026-01-01T00:00:00Z"
  }
}
```

### 3.6 Validation

OrchSpec documents must pass 21 semantic validation rules:

- **SEM001–SEM003**: Structural integrity (entry points, edges, cycles)
- **SEM004–SEM006**: Reference integrity (integrations, secrets)
- **SEM007–SEM009**: ID uniqueness, sequential branching, schedule coherence
- **SEM010**: Category–executor compatibility
- **SEM011–SEM012**: Graph connectivity (reachability, connectedness)
- **SEM013**: Retry policy coherence
- **SEM014**: Resource request ≤ limit
- **SEM015**: Security context coherence
- **SEM016–SEM017**: I/O paths and data flow compatibility
- **SEM018**: Condition expression syntax
- **SEM019**: Integration type ↔ IO kind compatibility
- **SEM020**: Timeout vs schedule interval
- **SEM021**: Unused parameters and secrets

---

## 4. The Compiler Bridge

The `pipespec2orchspec` compiler transforms PipeSpec → OrchSpec deterministically.

### Normalization Rules

| PipeSpec Input | OrchSpec Output |
|---------------|-----------------|
| `executor_type: "python"` | `executor.type: "python_script"` |
| `executor_type: "http"` | `executor.type: "http_request"` |
| `executor_type: "docker"` | `executor.type: "container"` |
| `parameter.type: "integer"` | `parameter.type: "INT"` |
| `parameter.type: "float"` | `parameter.type: "FLOAT"` |
| `integration.type: "objectstore"` | `integration.type: "object_store"` |
| `io.format: "TXT"` | `io.format: "text"` |
| `schedule: "manual"` | `schedule.enabled: false` |
| `edge_type: "conditional"` | `edge_type: "success"` (condition preserved) |

### Canonical IDs

IDs are canonicalized: lowercased, non-alphanumeric → underscores, collisions resolved with numeric suffixes.

---

## 5. Projection Model

OrchSpec documents are projected onto orchestrator targets through adapters.

### Supported Targets (Real Projections)

| Orchestrator | Output Format | Key Constructs |
|-------------|--------------|----------------|
| **Airflow 2.x** | Python (TaskFlow API) | `@dag`, `@task`, `SimpleHttpOperator`, `EmailOperator`, `BashOperator`, `DockerOperator` |
| **Prefect 2.x** | Python | `@flow`, `@task`, retries, timeouts, `.serve()` |
| **Dagster** | Python | `@asset`, `AssetExecutionContext`, `Definitions`, `ScheduleDefinition` |
| **Argo Workflows** | YAML | `WorkflowTemplate`, `CronWorkflow`, DAG tasks, `retryStrategy` |

---

## 6. Extensibility

### PipeSpec Extensions
- `"category": "Custom"` for domain-specific component types
- `"executor_type": "custom"` for non-standard executors
- `extensions: {}` field for org-specific metadata

### OrchSpec Extensions
- `"executor": {"type": "custom", "custom_class": "..."}` for custom executors
- `"category": "Custom"` for domain-specific steps
- `"integration": {"type": "custom"}` for unlisted systems
- `metadata.labels` and `metadata.tags` for arbitrary key-value metadata
- JSON Schema `allOf` wrappers for domain-specific required fields
- Pluggable adapter framework for new orchestrator targets

---

## 7. Common Patterns

### Pattern: Simple Sequential ETL

```
Extract → Transform → Load
```

- PipeSpec: `"flow_structure": {"pattern": "sequential"}` with linear edges
- OrchSpec: `"flow": {"pattern": "sequential"}` — enforces no branching (SEM008)

### Pattern: Fan-Out / Parallel

```
         ┌→ Transform_A ─┐
Extract ─┤                ├→ Load
         └→ Transform_B ─┘
```

- PipeSpec: `"pattern": "dag"` with multiple outgoing edges from Extract
- OrchSpec: multiple edges from Extract, components execute concurrently

### Pattern: Conditional Branching

```
              ┌→ Path_A (if value > threshold)
Extract ──────┤
              └→ Path_B (if value <= threshold)
```

- PipeSpec: `"edge_type": "conditional"` with `"condition"` strings
- OrchSpec: edges with `"condition"` expressions, validated for syntax (SEM018)

### Pattern: Scheduled Pipeline

- PipeSpec: `"parameters": {"schedule": {"expression": {"default": "0 6 * * *"}}}`
- OrchSpec: `"schedule": {"enabled": true, "cron": "0 6 * * *"}`

---

## 8. Repository Map

| Repository | Contents |
|-----------|----------|
| [`aliduabubakari/opos`](https://github.com/aliduabubakari/opos) | Standard definition, architecture, conformance |
| [`aliduabubakari/pipespec`](https://github.com/aliduabubakari/pipespec) | PipeSpec schema, validator, LLM tools |
| [`aliduabubakari/orchspec`](https://github.com/aliduabubakari/orchspec) | OrchSpec schema, compiler, validators, adapters |

---

## 9. Quick Reference

### PipeSpec

| Field | Required | Type |
|-------|----------|------|
| `pipespec_version` | Yes | `"1.0"` |
| `pipeline_summary.name` | Yes | string |
| `pipeline_summary.description` | No | string |
| `pipeline_summary.flow_patterns` | Yes | array of FlowPattern |
| `pipeline_summary.complexity` | Yes | `low` / `medium` / `high` |
| `components[].id` | Yes | string (pattern: alphanumeric + `_-`) |
| `components[].name` | Yes | string |
| `components[].category` | Yes | ComponentCategory enum |
| `components[].executor_type` | Yes | ExecutorType enum |
| `components[].io_spec` | Yes | array (≥1) |
| `flow_structure.pattern` | Yes | FlowPattern enum |
| `flow_structure.entry_points` | Yes | array (≥1) |
| `flow_structure.edges` | Yes | array |

### OrchSpec

| Field | Required | Type |
|-------|----------|------|
| `orchspec_version` | Yes | `"1.0"` |
| `pipeline_id` | Yes | string (pattern: `^[a-z0-9][a-z0-9_-]*$`) |
| `description` | Yes | string |
| `metadata.name` | Yes | string |
| `metadata.owner` | Yes | string |
| `metadata.domain` | Yes | string |
| `metadata.complexity` | Yes | `low` / `medium` / `high` |
| `components` | Yes | array (≥1) |
| `components[].id` | Yes | string |
| `components[].category` | Yes | ComponentCategory enum |
| `components[].executor.type` | Yes | ExecutorType enum |
| `flow.pattern` | Yes | FlowPattern enum |
| `flow.entry_points` | Yes | array (≥1) |
| `flow.edges` | Yes | array |
