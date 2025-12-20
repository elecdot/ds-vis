---
bound_phase: P0.6
version: v0.6
status: Active
last_updated: 2025-12-15
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.6 — Timed Animation & Playback Controls
- Scope: 在 L2 微步骤基础上加入可见动画过渡与基础播放控制/开关。
- Completion highlights:
  - Renderer 支持基于 `duration_ms` 的同步插值：`SET_POS` 线性移动、`SET_STATE` 颜色插值、CREATE/DELETE 的淡入淡出；全局速度因子可调并持久，动画可开关。
  - UI 播放控制：Play/Pause/Step/速度倍率（0.5/1/2），单步阻塞不续播；动画开关用于防止阻塞，快速验收。
  - List 插入微步骤、非追加式布局与高亮演示保持可播放；Dev 菜单可结合开关/速度复用。
  - 测试覆盖动画路径与播放控制行为；全套 pytest/ruff/mypy 通过。
- Active assumptions/limitations:
  - 动画为同步阻塞插值（qWait），长时长/大规模可能卡 UI；无 seek/倒播/skip，帧率与缓动固定（线性，<=10 帧）。
  - 支持的结构/命令仍仅 list create/delete/insert；其他模型为空壳，ID 稳定性未落地。
  - Renderer 配色/形状仍硬编码；`CREATE_NODE.data.kind` 未强制。
  - Layout 仍左对齐、固定尺寸、有状态顺序执行；未引入共享的 Metrics/Style 配置来适配不同节点形态。
  - UI 仍是 Dev playground：单场景，无多 Timeline 管理。
  - Qt 测试依赖 `QT_QPA_PLATFORM=offscreen`；运行 `uv run` 时如遇缓存权限需设置 `UV_CACHE_DIR=./tmp/uv-cache`。

### High-order issues (critical)
- 时间控制阻塞，缺少 skip/seek/倒播与非阻塞调度；性能/体验需迭代。
- 命令/模型覆盖面有限：仅 list；扩展 BST/GitGraph 需补注册表、模型与测试。
- 结构 ID 稳定性仅在 list 覆盖，其他结构仍为索引派生。
- 多结构视觉分区（结构容器框/区域分配）未落地，混排可能冲突。

## Planned Next Phase: P0.7 — Non-blocking Animation & Broader Coverage
- 核心目标：降低动画对 UI 的阻塞，引入跳过/seek 能力，并拓展更多结构。
- Scope（初版）:
  - Renderer 动画异步化或减少主线程阻塞；增加“跳过动画”快捷操作；可选缓动策略。
  - UI 播放控制扩展：可选 skip/rest 钩子，基础 seek 方案设计（可能需状态重建或快照）。
  - 模型/命令扩展优先级评估（BST/GitGraph），补注册表与最小动画走通。
- 延迟项：多场景/多 Timeline 并行管理、皮肤/主题、深度播放控制。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
