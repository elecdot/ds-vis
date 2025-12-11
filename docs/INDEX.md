# Documentation Registry & Version Control

This file tracks the current version of design documents and their binding to source code.

> **Protocol for Agents:**
> 1. **Check**: Before writing code, check this table. If you are modifying a "Bound Path", read the corresponding document.
> 2. **Update**: If your code changes the design (e.g., new OpCode, new Model method), you **MUST** update the document and increment the version here.

| Document | Version | Status | Bound Code Paths | Last Updated |
| :--- | :--- | :--- | :--- | :--- |
| [REQUEST.md](./REQUEST.md) | v0.1 | Stable | N/A | 2025-12-11 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | v0.2 | Stable | `src/ds_vis/` (Global Structure) | 2025-12-11 |
| [OPS_SPEC.md](./OPS_SPEC.md) | v1.0 | Stable | `src/ds_vis/core/ops/` | 2025-12-11 |
| [ANIMATION_REQUIREMENTS.md](./ANIMATION_REQUIREMENTS.md) | v0.1 | Draft | `src/ds_vis/core/models/`, `layout/`, `renderers/` | 2025-12-11 |
| [ENVIRONMENT.md](./ENVIRONMENT.md) | v0.2 | Stable | `pyproject.toml`, `.github/` | 2025-12-11 |
| [DEV_KNOWLEDGE_BASE.md](./DEV_KNOWLEDGE_BASE.md) | v0.1 | Living | N/A | 2025-12-11 |

## Versioning Convention
- **v0.x**: Draft / Prototype phase.
- **v1.x**: Stable protocol (breaking changes require v2.x).
- **Patch (v1.0.1)**: Clarifications, typos (no code changes required).
