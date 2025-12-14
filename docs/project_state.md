---
bound_phase: P0.3
version: v0.2
status: Active
last_updated: 2025-12-14
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.3 — Pipeline Hardening (list focus)
- Scope: hardened path Command → SceneGraph → Layout → Renderer with list create/delete and dev UI hooks.
- Completion highlights:
  - SceneGraph uses a handler注册表；unsupported命令抛 `CommandError`，DELETE 拆分为 DELETE_STRUCTURE / DELETE_NODE。
  - List IDs 单调不复用；支持 delete-all / delete-index，边 ID 映射包含结构/方向/端点。
  - SimpleLayout 删除/重建后刷新一行定位；PySide6 renderer 支持 step 级入口与消息显示。
  - 测试重组按域划分（core/renderers/ui）；新增错误路径、ID/布局稳定性、消息显示用例。
- Active assumptions/limitations:
  - Command 面极小：仅 list 的 CREATE_STRUCTURE/DELETE_STRUCTURE/DELETE_NODE；payload 校验为最小必填/类型检查。
  - UI controls: dev-only menu; single-scene、单次播放；消息呈现仅在 renderer 内部文本项，未与状态栏联动。
  - Qt tests rely on `QT_QPA_PLATFORM=offscreen` for headless runs.
  - Layout: 单行、全局 `start_y`、无多结构间距；每步全量 SET_POS（无脏检查）；仅基于当前节点快照。
  - Renderer: 仍忽略 `duration_ms`；无播放控制；视觉硬编码。
  - Tests：覆盖 list 创建/删除/布局刷新和错误路径；但 timing、BST/GitGraph、细粒度动画仍缺。
  - BST/GitGraph models 仍为空壳；List 动画停留在 L1（结果态）。

### High-order issues (critical)
- Command surface/校验仍最小化；后续命令扩展需引入更严格的 schema（避免 handler 逻辑分散）。
- 除 list 外的 ID 仍基于索引；删除/插入会导致漂移，需在其他结构落地单调 ID 与 EdgeKey。
- Layout 简化策略在多结构/动态场景下会错位或发膨胀的 SET_POS；需脏检查与多行/分组布局。
- Renderer 忽略时序，UI 无播放控制，难以暴露 timing/动画问题。

## Planned Next Phase: P0.4 — Feature Expansion (sketch)
- 扩展命令与模型：BST/GitGraph 逻辑与稳定 IDs；完善 EdgeKey 映射。
- 引入命令 payload schema/验证与 handler 注册表扩展；支持 INSERT/SEARCH 等。
- Layout 多结构间距/脏检查与更丰富的布局策略；Renderer/ UI 暴露时序与控制。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
