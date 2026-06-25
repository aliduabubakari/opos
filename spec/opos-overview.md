# OPOS Conformance Specification v1.0

This document defines what it means for an implementation to conform to the Open Pipeline Orchestration Specification (OPOS).

---

## 1. OPOS Standard Definition

OPOS defines two specification layers:

- **PipeSpec v1.0**: Extraction format for pipeline descriptions. Normative schema at [`pipespec_schema_v1.json`](https://github.com/aliduabubakari/pipespec/blob/main/schema/pipespec_schema_v1.json).
- **OrchSpec v1.0**: Canonical intermediate representation for pipeline orchestration. Normative schema at [`orchspec_schema_v1.json`](https://github.com/aliduabubakari/orchspec/blob/main/spec/orchspec_schema_v1.json).

An OPOS-conformant implementation MUST support both layers as defined below.

---

## 2. PipeSpec Conformance

### 2.1 Document Validity

A PipeSpec document is conformant if it validates against `pipespec_schema_v1.json` (JSON Schema Draft-07).

### 2.2 Required Capabilities

A PipeSpec-conformant tool MUST:

1. **Produce** PipeSpec documents that validate against the canonical schema
2. **Validate** PipeSpec documents against the canonical schema, returning structured errors with JSON Pointer paths
3. **Preserve** the `pipespec_version` field as `"1.0"`

A PipeSpec-conformant tool MAY:

- Accept YAML input by parsing it into a dict before schema validation
- Implement semantic validation beyond the schema (DAG cycles, reference integrity)
- Provide LLM-based generation from natural language descriptions
- Support correction/repair loops for invalid documents

### 2.3 Extension Policy

PipeSpec extensions MUST NOT:
- Remove or rename required fields from the canonical schema
- Change the type or enum values of existing fields

PipeSpec extensions MAY:
- Add optional fields under the `extensions` key at the top level or per component
- Use custom values for free-form fields like `executor_config` and `authentication`

---

## 3. OrchSpec Conformance

### 3.1 Document Validity

An OrchSpec document is conformant if it:

1. Validates against `orchspec_schema_v1.json` (JSON Schema Draft-07)
2. Passes all 21 semantic validation rules (SEM001–SEM021) as defined in the [OrchSpec specification](https://github.com/aliduabubakari/orchspec/blob/main/spec/orchspec-spec-v1.md)

### 3.2 Required Capabilities

An OrchSpec-conformant tool MUST:

1. **Compile** PipeSpec v1.0 documents into OrchSpec v1.0 documents deterministically (same input → byte-identical output)
2. **Validate** OrchSpec documents against the canonical JSON Schema and all 21 semantic rules
3. **Diff** OrchSpec documents semantically, reporting component, edge, and integration changes with breaking/non-breaking classification
4. **Project** OrchSpec documents onto at least one target orchestrator through an adapter conforming to the OrchSpecAdapter Protocol

An OrchSpec-conformant tool MAY:

- Support additional target orchestrators beyond the required minimum
- Implement strict mode where warnings are promoted to errors
- Provide additional semantic validation rules beyond SEM001–SEM021

### 3.3 Compiler Determinism

The compiler MUST produce byte-identical output given identical input. This requires:

1. **Canonical ordering**: Components topologically sorted, keys lexicographically sorted
2. **Normalization**: All types, IDs, and formats mapped to canonical forms
3. **Null omission**: Non-required null/empty values omitted from output

### 3.4 Adapter Protocol

Every adapter MUST implement:

```python
class OrchspecAdapter(Protocol):
    def capability(self) -> AdapterCapability: ...
    def validate_invariants(self, orchspec_doc: dict) -> list[str]: ...
    def project(self, orchspec_doc: dict) -> ProjectionResult: ...
```

`ProjectionResult` MUST include:
- `target`: Target orchestrator identifier
- `artifact_type`: String identifying the output format
- `content`: Dict containing the projected artifact (source code, YAML, etc.)

### 3.5 Extension Policy

OrchSpec extensions MUST NOT:
- Remove or rename required fields from the canonical schema
- Change existing enum values
- Break the determinism guarantee

OrchSpec extensions MAY:
- Add new optional fields through JSON Schema `allOf` wrapper schemas
- Add custom executor types using `executor.type: "custom"`
- Add custom integration types using `integration.type: "custom"`
- Add custom component categories using `category: "Custom"`
- Implement new orchestrator adapters
- Add semantic validation rules (numbered SEM022+)

---

## 4. Implementation Profiles

### 4.1 Full OPOS Implementation

Supports both layers completely:
- PipeSpec generation, validation, and LLM extraction
- PipeSpec → OrchSpec deterministic compilation
- OrchSpec validation (schema + 21 semantic rules)
- OrchSpec semantic diff
- Multi-orchestrator projection (at least one real adapter)

### 4.2 OrchSpec-Only Implementation

Supports only the canonical layer:
- Accepts PipeSpec documents and compiles to OrchSpec
- Validates and diffs OrchSpec documents
- Projects to target orchestrators

### 4.3 PipeSpec-Only Implementation

Supports only the extraction layer:
- Generates and validates PipeSpec documents
- May emit PipeSpec for downstream OrchSpec compilation

---

## 5. Version Compatibility

| OPOS Version | PipeSpec | OrchSpec |
|-------------|----------|----------|
| 1.0 | v1.0 | v1.0 |

Within a MAJOR version:
- Documents valid under v1.N MUST remain valid under v1.N+1
- New fields added in v1.N+1 MUST be optional
- New semantic rules added in v1.N+1 MUST be warnings by default

---

## 6. Normative References

- [PipeSpec v1.0 Schema](https://github.com/aliduabubakari/pipespec/blob/main/schema/pipespec_schema_v1.json)
- [OrchSpec v1.0 Schema](https://github.com/aliduabubakari/orchspec/blob/main/spec/orchspec_schema_v1.json)
- [OrchSpec v1.0 Specification](https://github.com/aliduabubakari/orchspec/blob/main/spec/orchspec-spec-v1.md)
- [OrchSpec Compiler Guide](https://github.com/aliduabubakari/orchspec/blob/main/docs/compiler-guide.md)
- [JSON Schema Draft-07](https://json-schema.org/draft-07/json-schema-release-notes.html)
- [Semantic Versioning 2.0.0](https://semver.org/)
