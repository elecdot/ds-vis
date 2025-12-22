---
bound_phase: P0.7
version: v1.0
status: Stable
last_updated: 2025-12-24
---

# Documentation Registry & Version Control

This file tracks the current version of design documents and their binding to source code.

> **Protocol for Agents:**
> 1. **Check**: Before writing code, check this table. If you are modifying a "Bound Path", read the corresponding document.
> 2. **Update**: If your code changes the design (e.g., new OpCode, new Model method), you **MUST** update the document and increment the version here.

Project state SSOT: see [project_state.md](./project_state.md) for the active phase, assumptions/limitations, and next-phase plan. This is declared here for discoverability; the registry below remains for doc binding.

| Document | Version | Status | Bound Phase | Bound Code Paths | Last Updated |
| :--- | :--- | :--- | :--- | :--- | :--- |
| [index.md](./index.md) | v1.0 | Stable | P0.7 | Documentation Registry System | 2025-12-24 |
| [project_state.md](./project_state.md) | v0.7.26 | Active | P0.7 | Project phase SSOT | 2025-12-22 |
| [requirements.md](./design/requirements.md) | v0.1 | Stable | P0.2 | N/A | 2025-12-14 |
| [architecture.md](./design/architecture.md) | v0.5 | Stable | P0.6 | `src/ds_vis/` (Global Structure) | 2025-12-15 |
| [scene_graph.md](./design/scene_graph.md) | v0.5 | Draft | P0.7 | `src/ds_vis/core/scene/` | 2025-12-24 |
| [renderer.md](./design/renderer.md) | v0.4.1 | Draft | P0.7 | `src/ds_vis/renderers/` | 2025-12-22 |
| [model.md](./design/model.md) | v0.8.1 | Draft | P0.7 | `src/ds_vis/core/models/` | 2025-12-22 |
| [layout.md](./design/layout.md) | v0.7.1 | Draft | P0.7 | `src/ds_vis/core/layout/` | 2025-12-22 |
| [ops_spec.md](./design/ops_spec.md) | v1.3 | Stable | P0.6 | `src/ds_vis/core/ops/` | 2025-12-20 |
| [animation.md](./design/animation.md) | v0.8 | Draft | P0.7 | `src/ds_vis/core/models/`, `layout/`, `renderers/` | 2025-12-24 |
| [dsl.md](./design/dsl.md) | v0.1 | Draft | P0.7 | `src/ds_vis/dsl/`, `src/ds_vis/ui/main_window.py` (Dev DSL hook), `src/ds_vis/dsl/cli.py` | 2025-12-24 |
| [json.md](./design/json.md) | v0.2 | Draft | P0.7 | `src/ds_vis/persistence/json_io.py` | 2025-12-22 |
| [llm.md](./design/llm.md) | v0.1 | Draft | P0.7 | `src/ds_vis/llm/` | 2025-12-24 |
| [environment.md](./engineering/environment.md) | v0.2 | Stable | P0.2 | `pyproject.toml`, `.github/` | 2025-12-14 |
| [tdd_guide.md](./engineering/tdd_guide.md) | v1.1 | Active | P0.3 | `tests/` (TDD workflow) | 2025-12-15 |
| [dev_kb.md](./engineering/dev_kb.md) | rolling | Living | P0.6 | N/A | 2025-12-21 |
| [dsl/parser.py](../src/ds_vis/dsl/parser.py) | v0.1 | Stub | P0.7 | DSL parsing (JSON shortcut) | 2025-12-24 |
| [dsl/cli.py](../src/ds_vis/dsl/cli.py) | v0.1 | Stub | P0.7 | CLI DSL/JSON runner | 2025-12-24 |
| [persistence/json_io.py](../src/ds_vis/persistence/json_io.py) | v0.1 | Stub | P0.7 | Command JSON import/export | 2025-12-24 |
| [PLAN.md](./PLAN.md) | v0.1 | Draft | P0.7 | Iteration roadmap | 2025-12-24 |
| [full_dev_guide.md](./engineering/full_dev_guide.md) | v0.1 | Draft | P0.7 | Full delivery workflow guide | 2025-12-24 |

## Documentation Reorganization (v0.1 — 2025-12-14)

As of December 14, 2025, the documentation structure has been reorganized for better navigation and mkdocs integration:

**Directory Changes:**
- `docs/design/` — Design and specification documents (requirements, architecture, ops, animation)
- `docs/engineering/` — Engineering and development knowledge (environment, dev KB)

**File Renames:**
- `REQUEST.md` → `design/requirements.md`
- `ARCHITECTURE.md` → `design/architecture.md`
- `OPS_SPEC.md` → `design/ops_spec.md`
- `ANIMATION_REQUIREMENTS.md` → `design/animation.md`
- `ENVIRONMENT.md` → `engineering/environment.md`
- `DEV_KNOWLEDGE_BASE.md` → `engineering/dev_kb.md`

**Impact:** All internal document links and external references must use the new paths. If you encounter a reference to an old path, update it to point to the new location. This change is tracked in the registry table above (version v0.2, updated 2025-12-14).

## Front Matter Metadata (Phase-Bound)

Every design/engineering document carries a YAML front matter block with:

- `bound_phase`: active delivery phase this document is aligned to (e.g., P0.2).
- `version`: document version per registry above.
- `status`: Stable / Draft / Living.
- `last_updated`: ISO date for the latest substantive touch.

This metadata is authoritative for doc status and should match the registry table. Update both when a document’s phase alignment or version changes.

## Versioning Convention
- **v0.x**: Draft / Prototype phase.
- **v1.x**: Stable protocol (breaking changes require v2.x).
- **Patch (v1.0.1)**: Clarifications, typos (no code changes required).
