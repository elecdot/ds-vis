---
bound_phase: P0.7
version: v0.4.1
status: Draft
last_updated: 2025-12-22
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
- 消息策略：SET_MESSAGE 默认锚定场景 bbox 顶部居中（PySide6 基线），若 show_messages=False 则忽略消息 Ops；后续可按结构 bbox 定制或提供富提示。

## 6. 形态扩展（P0.8 计划）

- 形状与容器：
  - 顺序表/栈：矩形单元 + 背景“桶”，栈为竖向堆叠、顺序表为横向；需支持单元尺寸/间距与容器边框样式。
  - Huffman：队列区节点可复用矩形/圆形，需能标记“候选队列”容器；树区仍用树节点形态。
  - Git DAG：小圆点 + 标签，支持 lane 间横向偏移，可能需要 edge label 或轻量箭头（占位）。
- 消息锚点：保持全局 bbox 顶部，但需预留按结构 bbox 的锚点以减少遮挡（与 UI 消息区协作）。
- 配置：通过 RendererConfig 或按 kind 的样式 registry 注入，不得硬编码在模型/SceneGraph。
- 容器支持：矩形单元与桶（bucket）、lane 标记均通过 CREATE_NODE 的 `shape`/`width`/`height` 渲染；状态变更对桶仅改描边色。

## 7. 扩展点

- 新 OpCode 的渲染：在 Renderer 添加 handler，保持默认回退。
- 新样式需求：通过配置（或未来 StyleRegistry）按 `kind` 选择样式。
- 非阻塞动画：可引入调度器或 Qt Animation，但必须保持 Step 语义不变（计划 P0.8）。

## 8. 当前限制（P0.7）

- 动画仍为同步阻塞插值，可能导致 UI 卡顿；max_frames/easing 仅占位。
- 消息锚定场景 bbox，未按结构/节点做精准定位；无富提示。
- 配置与 Layout 未联动（尺寸/间距仍在 SimpleLayout/TreeLayout 内硬编码）。

> 交叉引用：Ops 协议见 `ops_spec.md`，Style/Metrics 约束见 `architecture.md` 第 7 节。
