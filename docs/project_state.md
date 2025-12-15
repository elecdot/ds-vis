---
bound_phase: P0.5
version: v0.4
status: Active
last_updated: 2025-12-15
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.5 — L2 Animation Skeleton (List Insert)
- Scope: L2 微步骤落地（链表插入）、非追加式布局、基本可视高亮与 Dev 播放入口。
- Completion highlights:
  - `ListModel.insert` 拆解为 Highlight → Delete old edge → New node born (highlight) → Rewire → Restore；ID/EdgeKey 单调；增补越界/头尾/空表插入测试。
  - SceneGraph/schema 现支持 INSERT（list），并进行 index 范围校验；Command 验证覆盖缺失 value 等错误路径。
  - `SimpleLayout` 支持 `data.index` 插入顺序，删除/插入后整体重排；多结构堆叠与脏检查保留。
  - PySide6 renderer 支持 `SET_STATE`（含 `highlight`）作用于节点与边；视觉管线可播放 Step 序列。
  - UI Dev 菜单新增链表插入演示，基于 QTimer 按 Step 播放；保留快速创建/删除/重建钩子。
  - 测试补齐：插入边界、布局头插右移、边高亮、Dev 插入 demo 烟测，全套 pytest/ruff/mypy 通过。
- Active assumptions/limitations:
  - 支持的结构/命令仍仅 list 的 create/delete/insert；其他结构模型为空壳，ID 稳定性未落地。
  - Renderer 仍按 Step 结果跳变，忽略 `duration_ms`，无缓入/缓出/插值；颜色/形状硬编码。
  - UI 播放控制极简：仅 Dev 菜单串行播放，无暂停/seek/速度控制；单场景。
  - Layout 仍为有状态顺序执行，不支持 seek/回放；固定节点尺寸与左对齐假设未改。
  - Qt 测试依赖 `QT_QPA_PLATFORM=offscreen`；运行 `uv run` 时可能需设置 `UV_CACHE_DIR` 避免全局缓存权限问题。

### High-order issues (critical)
- 命令/模型覆盖面有限：仅 list create/delete/insert；扩展 BST/GitGraph 需补注册表、模型与测试。
- 时间语义缺失：renderer 无插值/时间控制，UI 无播放控制；难以暴露 timing/动画问题。
- 结构 ID 稳定性仅在 list 覆盖，其他结构仍为索引派生。

## Planned Next Phase: P0.6 — Timed Animation & Playback Controls
- 核心目标：在保持 Step 粒度的基础上加入“真动画”与基础播放控制。
- Scope（初版）:
  - Renderer 内对 `SET_POS`/`SET_STATE`/CREATE/DELETE 做插值或淡入淡出，使用 Step `duration_ms`（提供跳过动画开关）。
  - UI 播放控制：最小集的 play/pause/step/速度倍率，驱动 Step 播放而非结果跳变。
  - 设计与文档：更新 animation.md 说明默认缓动/节奏策略；评估 ops_spec 是否需要可选的动画 hint（优先保持协议稳定）。
- 延迟项：seek/倒播、多结构并行播放、皮肤/主题切换。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
