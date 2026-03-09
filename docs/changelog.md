# Changelog

## 1.1.0 - 2026-03-08
- Added strict PipeSpec profile schema and early compiler rejection (`COMP012`)
- Added machine-readable mapping spec (`spec/mappings/pipespec_to_opos_v1.json`)
- Expanded semantic validation with:
  - `SEM011` unreachable components
  - `SEM012` disconnected subgraphs
  - `SEM013` retry policy coherence checks
- Added strict semantic mode (`opos-validate --strict`) where `SEM010` is promoted to error
- Added adapter interfaces, registry, and stub adapters for multi-orchestrator projection

## 1.0.0 - 2026-03-04
- Added OPOS v1.0 schema and spec
- Added deterministic PipeSpec -> OPOS compiler
- Added `opos-validate` schema + semantic validation
- Added `opos-diff` semantic comparator
- Added fixtures, tests, and CI
