# OPOS — Open Pipeline Orchestration Specification

**OPOS** is the open standard for describing, compiling, and projecting data pipelines. It defines two specification layers that make pipeline meaning explicit, deterministic, and portable across any orchestrator.

---

## The Two Layers

```
┌──────────────────────────────────────────────────────────────────┐
│                          OPOS                                     │
│            Open Pipeline Orchestration Specification              │
│                                                                   │
│  ┌─────────────────────────┐          ┌────────────────────────┐ │
│  │       PipeSpec           │          │       OrchSpec         │ │
│  │    Extraction Layer      │  ───→    │    Canonical IR       │ │
│  │                          │          │                        │ │
│  │  • LLM-friendly          │          │  • Deterministic       │ │
│  │  • Human-oriented        │          │  • Machine-validated   │ │
│  │  • Flexible schema       │          │  • Strict schema       │ │
│  │  • Tolerates variation   │          │  • 21 semantic rules   │ │
│  │                          │          │  • Diffable            │ │
│  │  github.com/aliduabubakari│         │  • Projectable         │ │
│  │       /pipespec          │          │                        │ │
│  └─────────────────────────┘          │  github.com/aliduabubakari│
│                                        │       /orchspec         │ │
│                                        └───────────┬────────────┘ │
│                                                    │              │
│                                                    ▼              │
│                                        ┌────────────────────────┐ │
│                                        │   Target Orchestrators  │ │
│                                        │                        │ │
│                                        │  Airflow  •  Prefect   │ │
│                                        │  Dagster  •  Argo      │ │
│                                        │  Kestra   •  Kubeflow  │ │
│                                        │  Flyte    •  (more…)   │ │
│                                        └────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### PipeSpec — The Extraction Layer

**Repository:** [github.com/aliduabubakari/pipespec](https://github.com/aliduabubakari/pipespec)

PipeSpec is the *intent layer* — an LLM-friendly, human-oriented format for extracting pipeline descriptions from natural language or code. It captures the orchestration skeleton without embedding business logic payloads.

- Designed for LLMs to generate from natural language descriptions
- Flexible schema with nulls, free-form strings, optional fields
- Captures components, flow topology, I/O specs, parameters, integrations
- Non-deterministic by design — two runs may produce structurally different but semantically equivalent output

### OrchSpec — The Canonical IR

**Repository:** [github.com/aliduabubakari/orchspec](https://github.com/aliduabubakari/orchspec)

OrchSpec is the *canonical layer* — a deterministic, strictly validated intermediate representation produced by compiling PipeSpec. It is the single source of truth for pipeline definition and the input for multi-orchestrator projection.

- Deterministic compilation (same PipeSpec → byte-identical OrchSpec)
- 21 semantic validation rules (SEM001–SEM021)
- Real adapter projectors for Airflow, Prefect, Dagster, and Argo Workflows
- Stub adapters for Kestra, Kubeflow, and Flyte
- Semantic diff engine for CI/CD pipeline change auditing
- 112 tests ensuring correctness

---

## Why Two Layers?

| Concern | PipeSpec | OrchSpec |
|---------|----------|----------|
| **Audience** | LLMs, humans reading extraction output | Machines, CI/CD pipelines, orchestrator adapters |
| **Schema strictness** | Loose — nulls, free-form strings | Strict — enums, patterns, required fields |
| **Determinism** | Not guaranteed | Guaranteed (byte-identical output) |
| **Validation depth** | Schema only | Schema + 21 semantic rules + adapter invariants |
| **Purpose** | Describe what the pipeline *is* | Define what the pipeline *will execute* |

This separation follows a proven pattern: the extraction layer optimizes for *input flexibility* (LLMs are imperfect), while the canonical layer optimizes for *output reliability* (CI/CD and orchestrator codegen need guarantees).

### The Transformation Layer — OTS

OPOS addresses the **orchestration layer** — what components exist, how they connect, and how they're scheduled. For the **transformation layer** — what SQL or code actually runs inside each component — OPOS references the [Open Transformation Specification (OTS)](https://github.com/francescomucio/open-transformation-specification) as the complementary standard.

OrchSpec's `ots_export` field maps orchestration components to OTS transformation definitions, linking the two layers. See the [architecture document](docs/architecture.md#5-the-transformation-layer--ots) for details on how OTS and OPOS work together.

---

## The Full Pipeline Lifecycle

```
Natural Language / Code Description
        │
        ▼  [LLM Extraction]
   PipeSpec v1.0                          ← Extraction layer
   (flexible, LLM-friendly)
        │
        ▼  [pipespec2orchspec compiler]   ← Deterministic compilation
   OrchSpec v1.0                          ← Canonical layer
   (strict, validated, diffable)
        │
        ▼  [Adapter projection]           ← Multi-orchestrator emission
   ┌────┴────┬────────┬─────────┐
   ▼         ▼        ▼         ▼
Airflow   Prefect  Dagster    Argo
  DAG      Flow     Assets   Workflow
```

Each layer is independently versioned, tested, and extensible. The compiler guarantees that the same PipeSpec input always produces the same OrchSpec output, enabling reproducible pipelines across teams and environments.

---

## Repository Map

| Layer | Repository | Contents |
|-------|-----------|----------|
| **Specification** | `aliduabubakari/opos` (this repo) | Standard definition, architecture, conformance criteria |
| **Extraction** | [`aliduabubakari/pipespec`](https://github.com/aliduabubakari/pipespec) | PipeSpec schema, validator, LLM generation tools |
| **Canonical IR** | [`aliduabubakari/orchspec`](https://github.com/aliduabubakari/orchspec) | OrchSpec schema, compiler, validator, diff, adapters |

---

## Conformance

An implementation conforms to the OPOS standard if:

1. It produces PipeSpec documents that validate against `pipespec_schema_v1.json`
2. It accepts PipeSpec documents and produces OrchSpec documents that validate against `orchspec_schema_v1.json`
3. Its OrchSpec compiler produces deterministic output (same input → identical output)
4. Its OrchSpec validator enforces SEM001–SEM021 as defined in the OrchSpec specification
5. It implements the OrchSpecAdapter Protocol for at least one target orchestrator

See [`spec/opos-overview.md`](spec/opos-overview.md) for the full conformance definition.

---

## Contributing

OPOS welcomes contributions across all three repositories:

- **Standard changes** (this repo): Open an issue to discuss proposed changes to the specification architecture, conformance criteria, or layer definitions.
- **PipeSpec changes** ([pipespec](https://github.com/aliduabubakari/pipespec)): Schema extensions, new validator rules, LLM provider support.
- **OrchSpec changes** ([orchspec](https://github.com/aliduabubakari/orchspec)): New adapters, validation rules, compiler improvements.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for detailed contribution guidelines.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

## Links

- [PipeSpec Repository](https://github.com/aliduabubakari/pipespec)
- [OrchSpec Repository](https://github.com/aliduabubakari/orchspec)
- [OTS — Open Transformation Specification](https://github.com/francescomucio/open-transformation-specification)
- [Architecture Document](docs/architecture.md)
- [Conformance Specification](spec/opos-overview.md)
- [Changelog](CHANGELOG.md)
