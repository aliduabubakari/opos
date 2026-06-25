# Contributing to OPOS

OPOS is an open standard. Contributions can target any of the three repositories that make up the specification.

---

## Repository Map

| Repository | What to contribute |
|-----------|-------------------|
| **`aliduabubakari/opos`** (this repo) | Standard architecture, conformance criteria, layer definitions, documentation |
| **`aliduabubakari/pipespec`** | PipeSpec schema, validator, LLM generation tools, extraction examples |
| **`aliduabubakari/orchspec`** | OrchSpec schema, compiler, validators, adapters, tests |

---

## Contributing to the OPOS Standard (this repo)

This repository defines the OPOS standard itself — the two-layer architecture, the design rationale, and the conformance criteria.

### What belongs here

- Architecture documentation and diagrams
- Conformance specification updates
- Layer relationship definitions
- Standard versioning decisions
- Cross-layer integration patterns

### What does NOT belong here

- Code (that lives in pipespec or orchspec repos)
- Schemas (canonical schemas live in their respective repos)
- Tests (tests live in implementation repos)
- Tooling (CLI, CI, build systems live in implementation repos)

### Process

1. **Open an issue** describing the proposed change to the standard
2. **Discuss** the change's impact on both layers
3. **Update** the relevant files:
   - `README.md` — if the standard overview changes
   - `docs/architecture.md` — if the architecture or design rationale changes
   - `spec/opos-overview.md` — if conformance criteria change
   - `CHANGELOG.md` — always update with the change
4. **Open a PR** with a clear description referencing the issue

---

## Contributing to PipeSpec or OrchSpec

For implementation-level contributions, see the contribution guides in each repository:

- **PipeSpec**: [github.com/aliduabubakari/pipespec](https://github.com/aliduabubakari/pipespec) — see `CONTRIBUTING.md`
- **OrchSpec**: [github.com/aliduabubakari/orchspec](https://github.com/aliduabubakari/orchspec) — see `CONTRIBUTING.md`

Common contribution types:

### PipeSpec
- Schema extensions (new optional fields)
- New LLM provider integrations
- Validator improvements
- Example pipeline documents

### OrchSpec
- New orchestrator adapters (see the [OrchSpec CONTRIBUTING.md](https://github.com/aliduabubakari/orchspec/blob/main/CONTRIBUTING.md) for a step-by-step guide)
- New semantic validation rules (SEM022+)
- Compiler improvements
- Test coverage expansion
- Documentation

---

## Code of Conduct

Be respectful, constructive, and inclusive. Harassment or disrespectful behavior will not be tolerated.

---

## Questions?

Open an issue in the relevant repository:

- Standard questions → `aliduabubakari/opos`
- PipeSpec questions → `aliduabubakari/pipespec`
- OrchSpec questions → `aliduabubakari/orchspec`
