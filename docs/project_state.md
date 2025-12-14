---
bound_phase: P0.2
version: v0.1
status: Stable
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
  - Unsupported commands return empty timelines (no error surface yet).
  - Layout is naive, append-only; delete/reflow not handled; single-row placement only.
  - Renderer ignores `duration_ms`; steps apply immediately.
  - BST/GitGraph models are stubs emitting empty timelines.
  - Renderer visuals are hardcoded (colors/shapes); timing support planned next phase.
  - UI controls are minimal (dev playground); no play/pause/step/speed.
  - Test coverage is thin; missing delete/reinsert ID stability, layout reflow, timing semantics, and BST/GitGraph ops.
  - Command enum/routing are rigid; handler registry and payload validation are pending.

### High-order issues (critical)
- Silent no-op commands can mask structural bugs and cause positional drift; treat unsupported commands as errors before P0.3 or expect hard-to-debug timelines.
- Model-generated IDs are index-based; deletes/inserts will rename nodes/edges and break animation continuity. Define stable, monotonic IDs per structure before adding more ops.

## Planned Next Phase: P0.3 — Pipeline Hardening (Minimal Scope)
- Capability goals:
  - SceneGraph rejects unsupported commands with surfaced errors; `CREATE_STRUCTURE` has minimal payload validation.
  - ListModel uses structure-local monotonic IDs (no index-based reuse) and keeps edge IDs stable through delete/recreate flows.
  - SimpleLayout can refresh positions after deletions/recreates (single-row layout retained).
  - Renderer accepts `duration_ms` but may still apply steps immediately; API shape remains stable for future timing work.
  - Tests cover the above (error path, ID stability, layout refresh).
- Design decision: finalize the SceneGraph error contract for unsupported/invalid commands (error vs. no-op) and record it in docs.


## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
