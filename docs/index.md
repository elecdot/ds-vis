# Documentation Registry & Version Control (v0.1)

This file tracks the current version of design documents and their binding to source code.

> **Protocol for Agents:**
> 1. **Check**: Before writing code, check this table. If you are modifying a "Bound Path", read the corresponding document.
> 2. **Update**: If your code changes the design (e.g., new OpCode, new Model method), you **MUST** update the document and increment the version here.

| Document | Version | Status | Bound Code Paths | Last Updated |
| :--- | :--- | :--- | :--- | :--- |
| [index.md](./index.md) | v0.1 | Stable | Documentation Registry System | 2025-12-14 |
| [requirements.md](./design/requirements.md) | v0.1 | Stable | N/A | 2025-12-11 |
| [architecture.md](./design/architecture.md) | v0.2 | Stable | `src/ds_vis/` (Global Structure) | 2025-12-11 |
| [ops_spec.md](./design/ops_spec.md) | v1.0 | Stable | `src/ds_vis/core/ops/` | 2025-12-11 |
| [animation.md](./design/animation.md) | v0.1 | Draft | `src/ds_vis/core/models/`, `layout/`, `renderers/` | 2025-12-11 |
| [environment.md](./engineering/environment.md) | v0.2 | Stable | `pyproject.toml`, `.github/` | 2025-12-11 |
| [dev_kb.md](./engineering/dev_kb.md) | rolling | Living | N/A | Always Current |

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

**Impact:** All internal document links and external references must use the new paths. If you encounter a reference to an old path, update it to point to the new location. This change is tracked in the registry table above (version v0.1, updated 2025-12-14).

## Versioning Convention
- **v0.x**: Draft / Prototype phase.
- **v1.x**: Stable protocol (breaking changes require v2.x).
- **Patch (v1.0.1)**: Clarifications, typos (no code changes required).
