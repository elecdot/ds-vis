---
bound_phase: P0.7
version: v0.2
status: Draft
last_updated: 2025-12-24
---

# RENDERER — 设计说明（轻量）

本文件描述 Renderer 的职责、输入输出与扩展点，避免写入具体 UI 实现细节。

## 1. 角色与职责

- 消费 `Timeline` 并按 Step 顺序渲染。
- 只负责“画面表现”，不改写 Model/SceneGraph 状态。
- 遵守 Ops 协议，保持跨渲染器一致语义。

## 2. 输入输出

- 输入：`Timeline`（`AnimationStep` 列表）。
- 输出：可视状态（节点/边/文本/提示）。

## 3. 约束与边界

- **不得**反向访问 Model 或 SceneGraph。
- **不得**直接操纵结构逻辑（只能消费 Ops）。
- **必须**支持 `SET_POS`、`SET_STATE`、CREATE/DELETE、SET_LABEL、消息 Ops。

## 4. 动画控制（P0.6 基线）

- 支持基于 `duration_ms` 的基础动画（线性插值、淡入淡出）。
- 支持全局速度因子与动画开关。
- Step 粒度播放，不支持 seek/倒播/skip（后续阶段扩展）。

## 5. 配置化（P0.7 增量）

- RendererConfig（当前 PySide6 实现）：
  - `node_radius`：默认 20
  - `colors`：状态颜色表（默认与旧版一致：normal/active/highlight/secondary/to_delete/faded/error）
  - `max_frames`：动画帧数上限（默认 10，保持原行为）
  - `show_messages`：是否渲染 SET_MESSAGE/CLEAR_MESSAGE（可禁用）
  - `easing`：占位（当前仅线性）
- 默认构造保持视觉/阻塞播放不变，配置为可选注入。
- 消息策略：固定 HUD 文本，若 show_messages=False 则忽略消息 Ops。

## 6. 扩展点

- 新 OpCode 的渲染：在 Renderer 添加 handler，保持默认回退。
- 新样式需求：通过配置（或未来 StyleRegistry）按 `kind` 选择样式。
- 非阻塞动画：可引入调度器或 Qt Animation，但必须保持 Step 语义不变（计划 P0.8）。

## 7. 当前限制（P0.7）

- 动画仍为同步阻塞插值，可能导致 UI 卡顿；max_frames/easing 仅占位。
- 消息为固定位置文本，无节点锚定/富提示。
- 配置与 Layout 未联动（尺寸/间距仍在 SimpleLayout 内硬编码）。

> 交叉引用：Ops 协议见 `ops_spec.md`，Style/Metrics 约束见 `architecture.md` 第 7 节。
