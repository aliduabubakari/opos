# AGENT.md — OPOS Meta-Project Guide

> **Guidance for AI coding agents working on the OPOS standard meta-project.**
>
> OPOS (Open Pipeline Orchestration Specification) is the umbrella standard that defines two specification layers:
> PipeSpec (extraction) and OrchSpec (canonical IR). This repository is the **meta-project** —
> it defines the standard architecture, conformance criteria, and cross-layer relationships.
> Code, schemas, and tests live in the implementation repositories.

---

## 1. Project Identity

| Item | Value |
|------|-------|
| **Standard name** | OPOS — Open Pipeline Orchestration Specification |
| **Repository** | `aliduabubakari/opos` |
| **Role** | Meta-project: architecture, conformance, cross-layer docs |
| **Contains code?** | No — code lives in pipespec and orchspec repos |
| **License** | Apache-2.0 |

### Implementation Repositories

| Layer | Repository | Contains |
|-------|-----------|----------|
| **Extraction** | [`aliduabubakari/pipespec`](https://github.com/aliduabubakari/pipespec) | PipeSpec schema, validator, LLM generation tools |
| **Canonical** | [`aliduabubakari/orchspec`](https://github.com/aliduabubakari/orchspec) | OrchSpec schema, compiler, validators, diff, adapters |

---

## 2. Repository Layout

```
opos/
├── README.md              ← Umbrella: what OPOS is, two layers, links to repos
├── LICENSE                ← Apache 2.0
├── CHANGELOG.md           ← Standard version history
├── CONTRIBUTING.md        ← How to contribute to the standard (and where code goes)
├── AGENT.md               ← This file — AI coding agent guide
├── skills.md              ← LLM reference for OPOS pipeline generation
├── technical.md           ← Technical design rationale
├── docs/
│   └── architecture.md    ← Full architecture: design rationale, layers, compiler bridge
└── spec/
    └── opos-overview.md   ← Normative conformance specification
```

---

## 3. What This Repo Is (and Isn't)

### This repo IS:
- The canonical definition of the OPOS standard
- The home for architecture documentation
- The place for conformance criteria
- The entry point for understanding the two-layer model
- A reference for WHY PipeSpec + OrchSpec exist as separate layers

### This repo IS NOT:
- A code repository (no `src/`, no `pyproject.toml`)
- A schema repository (schemas live in pipespec/orchspec repos)
- A test repository (tests live in orchspec)
- A package on PyPI

---

## 4. Key Concepts for Agents

### 4.1 The Two-Layer Model

OPOS = PipeSpec + OrchSpec. This is the fundamental concept. Everything in this repo explains or supports this model.

- **PipeSpec** = extraction layer (LLM-friendly, flexible, non-deterministic)
- **OrchSpec** = canonical layer (strict, deterministic, validated, projectable)

### 4.2 Integration Complexity Reduction

Without OPOS: N description formats × M orchestrators = N×M mappings.
With OPOS: N + M mappings through a stable intermediate representation.

### 4.3 Cross-Repository Workflows

When working on OPOS, understand which change goes where:

| Type of change | Goes in this repo? | Where it actually goes |
|---------------|-------------------|----------------------|
| New validator rule | No | `orchspec` repo (`src/.../validation/semantic.py`) |
| New adapter | No | `orchspec` repo (`src/.../adapters/`) |
| Schema change (PipeSpec) | No | `pipespec` repo (`schema/`) |
| Schema change (OrchSpec) | No | `orchspec` repo (`spec/`) |
| Standard architecture doc | **Yes** | `docs/architecture.md` |
| Conformance criteria | **Yes** | `spec/opos-overview.md` |
| README update | **Yes** | `README.md` |
| Changelog | **Yes** | `CHANGELOG.md` |
| AGENT.md / skills.md | **Yes** | This file / `skills.md` |

### 4.4 When to Update This Repo

Update the OPOS meta-project when:
- The relationship between PipeSpec and OrchSpec changes
- A new implementation profile is defined
- Conformance criteria change
- The standard version is bumped
- Architecture documentation needs updating

---

## 5. Agent Conventions

### File Editing
- Use exact-text replacements via `edit` tool
- Keep cross-references accurate (GitHub URLs to pipespec/orchspec repos)
- Maintain consistent naming: "OPOS" for the standard, "PipeSpec" for extraction, "OrchSpec" for canonical

### Cross-Repo Awareness
- When asked about PipeSpec schema details, refer to the pipespec repo
- When asked about OrchSpec validation rules, refer to the orchspec repo
- This repo links to both but does not duplicate their content

### Naming
- OPOS = Open Pipeline Orchestration Specification (the whole thing)
- PipeSpec = Pipeline Specification (extraction layer)
- OrchSpec = Orchestration Specification (canonical layer)
- Never use "OPOS" to mean OrchSpec or vice versa — they are distinct layers

---

## 6. Common Tasks

### Update architecture documentation
Edit `docs/architecture.md` — this is the primary design document.

### Update conformance criteria
Edit `spec/opos-overview.md` — this defines what "OPOS-conformant" means.

### Add a new standard version
1. Update `CHANGELOG.md` with the new version
2. Update version references in `README.md` and `spec/opos-overview.md`
3. If layer versions changed, update the compatibility table

### Respond to "what is OPOS?"
Point to `README.md` — it has the diagram, layer descriptions, and links.
