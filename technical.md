# OPOS Technical Design

## 1. Purpose

OPOS (Open Pipeline Orchestration Specification) is a universal standard for pipeline orchestration.

It separates three concerns across two layers:

1. **Extraction** (PipeSpec): Understanding pipeline intent from natural language or code.
2. **Canonicalization** (OrchSpec): Normalizing that intent into a stable, deterministic form.
3. **Projection** (OrchSpec Adapters): Projecting the canonical form into orchestrator-specific outputs.

---

## 2. Why Two Layers?

### The Integration Problem

Without a standard intermediate representation, every pipeline description format must map directly to every target orchestrator:

```
N description formats × M orchestrators = N×M integrations
```

Each new description format requires M new mappings. Each new orchestrator requires N new mappings. The cost grows multiplicatively.

### The OPOS Solution

By inserting a stable canonical intermediate representation between extraction and execution:

```
N description formats → 1 canonical IR → M orchestrators = N + M integrations
```

- **N mappings** from description formats → PipeSpec (extraction)
- **1 deterministic compiler** from PipeSpec → OrchSpec
- **M mappings** from OrchSpec → orchestrator targets (projection)

Each mapping is built once and reused across all other integrations.

---

## 3. Layer Separation Rationale

### Why not one format?

A single format would need to serve two conflicting audiences:

| Requirement | For LLMs (extraction) | For CI/CD (canonical) |
|------------|----------------------|----------------------|
| Schema strictness | Loose — tolerate LLM variation | Strict — reject ambiguity |
| Determinism | Not needed | Critical — byte-identical output |
| Human readability | High — descriptive enums | Medium — machine-oriented |
| Null handling | Accept nulls liberally | Omit nulls for determinism |

Combining these requirements forces compromises. PipeSpec optimizes for the LLM use case; OrchSpec optimizes for the machine use case. The compiler bridges them with a deterministic, tested transformation.

### Analogy: Markdown → HTML

- **PipeSpec** is like Markdown: human-friendly, tolerant of variation, easy to generate from description.
- **OrchSpec** is like the DOM/HTML: machine-friendly, strictly structured, ready for rendering (projection).
- **The compiler** is like a Markdown parser: deterministic, normalized, produces consistent output.

---

## 4. The Compiler Bridge

The `pipespec2orchspec` compiler is the critical integration point. It must be:

### 4.1 Deterministic

Given the same PipeSpec input bytes and compiler version, the output must be byte-identical. This is achieved through:

- **Canonical ordering**: Topological sort of components, lexicographic key ordering, edge sorting by (from, to).
- **Normalization**: All types mapped to canonical forms, whitespace stripped, IDs canonicalized.
- **Null omission**: Non-required null/empty values removed from serialized output.

### 4.2 Profile-Aware

In strict mode, the compiler validates PipeSpec input against a profile schema that enforces `additionalProperties: false`, catching unknown fields and executor types before compilation.

### 4.3 Mapping-Driven

Transformation rules are declared in a machine-readable mapping spec (`pipespec_to_orchspec_v1.json`), not hardcoded. This allows the mapping to evolve independently of the compiler code.

---

## 5. Validation Architecture

OrchSpec validation is layered:

```
Document → [JSON Schema] → [SEM001–SEM021] → [Adapter Invariants] → Valid
              ↓ fail            ↓ fail              ↓ fail
           SCHEMA errors     SEM errors        Adapter violations
```

- **Layer 1 (Schema)**: Structural compliance — types, enums, required fields, patterns. Low-level, purely syntactic.
- **Layer 2 (Semantic)**: Cross-field integrity — graph connectivity, reference integrity, configuration coherence. Domain-aware.
- **Layer 3 (Adapter)**: Target-specific constraints — "Airflow doesn't support SQL natively", "Container executor needs an image".

This layered approach means each validation concern is independent and testable in isolation.

---

## 6. Projection Architecture

OrchSpec documents are projected onto orchestrator targets through a plugin-based adapter framework:

```
OrchSpec → [Adapter.validate_invariants()] → [Adapter.project()] → Target IR
```

### Adapter Protocol

```python
class OrchspecAdapter(Protocol):
    def capability(self) -> AdapterCapability:
        """Declare target, runtime style, supported executors."""

    def validate_invariants(self, orchspec_doc: dict) -> list[str]:
        """Target-specific pre-flight checks."""

    def project(self, orchspec_doc: dict) -> ProjectionResult:
        """Transform OrchSpec into target-native IR."""
```

### Real vs Stub Projections

- **Real projectors** (Airflow, Prefect, Dagster, Argo): Emit syntactically valid target-native code with operator mappings, dependency chains, retry/timeout configuration, and schedule handling.
- **Stub projectors** (Kestra, Kubeflow, Flyte): Emit placeholder IR that validates the interface contract. Ready for real generators to be implemented.

### Projection Outputs

| Adapter | Output Format | Artifact Type |
|---------|--------------|---------------|
| Airflow | Python (TaskFlow API) | `airflow_dag_python` |
| Prefect | Python (`@flow`/`@task`) | `prefect_flow_python` |
| Dagster | Python (`@asset`) | `dagster_definitions_python` |
| Argo | YAML (WorkflowTemplate) | `argo_workflow_template_yaml` |

---

## 7. Extensibility Design

OPOS is designed for extension at multiple layers without requiring changes to the core specification.

### PipeSpec Extensions
- `extensions: {}` at document and component level for org-specific fields
- `"executor_type": "custom"` for non-standard executors
- Free-form `executor_config` and `authentication` objects

### OrchSpec Extensions
- `"executor.type": "custom"` with `custom_class` identifier
- `"category": "Custom"` for domain-specific component types
- `"integration.type": "custom"` for unlisted external systems
- `metadata.labels` (string→string) and `metadata.tags` (string[]) for arbitrary metadata
- JSON Schema `allOf` wrapper schemas for domain-specific validation
- Pluggable adapter framework: new adapters implement the protocol and register in the registry

### Extension Principles
1. Canonical schemas remain untouched — extensions live in wrapper schemas or custom fields
2. Determinism is preserved — extensions must not introduce non-deterministic behavior
3. Backward compatibility — existing documents remain valid after extension
4. Independent versioning — extensions can version independently of the core standard

---

## 8. Versioning Strategy

Each layer is independently versioned following [SemVer](https://semver.org/):

| Component | Current Version | Scope |
|-----------|----------------|-------|
| PipeSpec Schema | 1.0 | Extraction format definition |
| OrchSpec Schema | 1.0 | Canonical IR definition |
| Compiler | 1.0 | PipeSpec → OrchSpec transformation |
| Adapters | 1.0 | OrchSpec → Target projection |

Within a MAJOR version:
- New optional fields are allowed
- New semantic rules are warnings by default
- Existing documents remain valid
- Determinism is preserved

---

## 9. Cross-Cutting Concerns

### Security
- Secret values are never embedded in PipeSpec or OrchSpec documents — only secret *references*
- Authentication methods are declared, credentials are resolved at runtime
- Container security contexts (non-root, read-only FS, capability dropping) are preserved through compilation

### Observability
- Logging configuration (level, format) propagates to target orchestrators
- Metrics standards (duration, success rate, row/byte counts) are declared
- Data lineage (sources, sinks, intermediate datasets) is captured in PipeSpec

### Reproducibility
- Provenance tracking: source file, generator, timestamp, model identifier
- Compiler version pinning for deterministic reproduction
- Golden regression testing for compiler output verification

---

## 10. Future Directions

- **Real projectors for remaining stubs**: Kestra (declarative YAML), Kubeflow (Pipelines SDK), Flyte (Flytekit)
- **Bidirectional compilation**: OrchSpec → PipeSpec reverse compiler for roundtrip validation
- **Visualization tools**: DAG graph rendering from OrchSpec documents
- **Schema registry**: Centralized repository of OPOS-compatible schemas and adapters
- **Enterprise extensions**: RBAC, multi-tenancy, approval workflows
