---
bound_phase: P0.2
version: v0.1
status: Active
last_updated: 2025-12-14
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.2 — Walking Skeleton (MVP pipeline)
- Scope: end-to-end path Command → SceneGraph → Layout → Renderer validated with list creation and a dev UI hook.
- Completion highlights:
  - Structural ops and timeline types defined and aligned with OPS spec.
  - Simple linear layout injects `SET_POS` and renderer places nodes/edges.
  - PySide6 renderer interprets ops (no timing yet) and supports state/label updates.
- Active assumptions/limitations:
  - Supported command: `CREATE_STRUCTURE` for `list`; others return empty timelines (no user-visible error yet).
  - UI controls: dev-only menu; single-scene, single-shot render; messages stored but not displayed.
  - Qt tests rely on `QT_QPA_PLATFORM=offscreen` for headless runs.
  - Layout: append-only, single row; delete/reflow not handled; multi-structure spacing not addressed.
  - Renderer: ignores `duration_ms`; no animation or playback controls; visuals hardcoded.
  - Tests are smoke-level (rendering, no-overlap); timing, delete/reinsert ID stability, layout reflow, BST/GitGraph ops untested.
  - Unsupported commands return empty timelines (no error surface yet).
  - BST/GitGraph models are stubs emitting empty timelines.
  - Command enum/routing are rigid; handler registry and payload validation are pending.

### High-order issues (critical)
- Silent no-op commands can mask structural bugs and cause positional drift; treat unsupported commands as errors before P0.3 or expect hard-to-debug timelines.
- Model-generated IDs are index-based; deletes/inserts will rename nodes/edges and break animation continuity. Define stable, monotonic IDs per structure before adding more ops.

## Planned Next Phase: P0.3 — Pipeline Hardening (summary only)
- Capability goals: surface errors for unsupported/invalid commands; adopt stable monotonic IDs for list nodes/edges; refresh single-row layout after mutations; keep renderer API accepting `duration_ms` and exposing a step-level entry; add tests that cover these contracts.
- Design decision to lock: SceneGraph error contract — unsupported/invalid commands raise `CommandError` (no silent no-op) and are documented.

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
