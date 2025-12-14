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
  - Supported command surface remains minimal: `CREATE_STRUCTURE` and `DELETE` (delete-all) for `list`; other commands raise `CommandError` and are unimplemented; command routing is hardcoded (no handler registry).
  - UI controls: dev-only menu; single-scene, single-shot render; messages stored but not displayed.
  - Qt tests rely on `QT_QPA_PLATFORM=offscreen` for headless runs.
  - Layout: single row with global `start_y`; no multi-structure spacing; always emits SET_POS for tracked nodes (no dirty check).
  - Renderer: ignores `duration_ms`; no animation or playback controls; visuals hardcoded.
  - Tests are smoke-level (rendering, no-overlap); timing, per-item delete, BST/GitGraph ops, and richer error-path checks untested.
  - BST/GitGraph models are stubs emitting empty timelines.
  - List animations停留在 L1（结果态）粒度，未覆盖 L2+ 细化步骤；其他结构无动画。

### High-order issues (critical)
- Command handling is rigid and DELETE 语义为 delete-all，未覆盖 per-item delete；需要 handler 注册表与严格 payload 校验，避免后续扩展时破坏语义。
- Model-generated IDs仍主要基于索引（list 之外）；删除/插入会导致 ID 漂移，需在更多结构中落地单调 ID。

## Planned Next Phase: P0.3 — Pipeline Hardening (summary only)
- Capability goals: surface errors for unsupported/invalid commands; adopt stable monotonic IDs for list nodes/edges; refresh single-row layout after mutations; keep renderer API accepting `duration_ms` and exposing a step-level entry; add tests that cover these contracts.
- Design decision to lock: 
  - SceneGraph error contract — unsupported/invalid commands raise `CommandError` (no silent no-op).
  - Animation granularity — accept L1 (result-only) steps for `create` ops in this phase; defer L2 (algorithmic steps) to future content phases.

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
