---
bound_phase: P0.4
version: v0.3
status: Active
last_updated: 2025-12-15
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.4 — Infrastructure & Scaffolding
- Scope: hardened path Command → SceneGraph → Layout → Renderer with list create/delete and dev UI hooks.
- Completion highlights:
  - Command schema + 模型 op 注册表落地（list），SceneGraph 通过注册表校验/路由，避免跨层访问模型内部。
  - BaseModel 抽象化（kind/node_count/apply_operation + 可插拔 ID 生成），ListModel 对齐并保持 ID/EdgeKey 单调。
  - SimpleLayout 升级：多结构垂直堆叠、脏检查、删除后行压缩；仍假设固定节点尺寸、左对齐。
  - List 命令流稳定：CREATE/DELETE_STRUCTURE/DELETE_NODE 覆盖，布局级联更新正确 rewiring。
  - 测试扩充覆盖 schema 校验、注册表映射、布局多结构/脏检查与删除重排。
- Active assumptions/limitations:
  - Command 面极小：仅 list 的 CREATE_STRUCTURE/DELETE_STRUCTURE/DELETE_NODE；schema/映射注册表仅覆盖 list，其他结构未注册。
  - UI controls: dev-only menu; single-scene、单次播放；消息呈现仅在 renderer 内部文本项，未与状态栏联动。
  - Qt tests rely on `QT_QPA_PLATFORM=offscreen` for headless runs.
  - Layout: stateful 顺序执行，不支持 seek/倒播；默认固定尺寸、左对齐；对齐策略单一，未支持树/DAG 居中。
  - Renderer: 仍忽略 `duration_ms`；无播放控制；视觉硬编码。
  - Tests：覆盖 list 创建/删除/布局刷新、schema 校验；但 timing、BST/GitGraph、细粒度动画仍缺。
  - BST/GitGraph models 仍为空壳；List 动画停留在 L1（结果态）。

### High-order issues (critical)
- Command 面与注册表仅覆盖 list；扩展 INSERT/BST/GitGraph 时需同步 schema/映射与文档。
- 除 list 外的 ID 仍基于索引；删除/插入会导致漂移，需在其他结构落地单调 ID 与 EdgeKey。
- Layout 仍是有状态的顺序引擎，不支持 seek；对齐策略和可变尺寸未实现，需在后续迭代扩展。
- Renderer 忽略时序，UI 无播放控制，难以暴露 timing/动画问题。

## Planned Next Phase: P0.5 — Timing & Renderer Controls (draft)
- 定义/实现时序与播放控制（播放/暂停/seek 方案），并评估布局/渲染的状态重建需求。
- 拓展命令面（至少 list INSERT，树/BST 基础操作）并同步 schema/注册表。
- 视情况推进 Renderer/UI 控制以暴露 timing/seek 问题，形成最小可操作的播放体验。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
