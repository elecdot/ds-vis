---
bound_phase: P0.6
version: v0.1
status: Draft
last_updated: 2025-12-15
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

## 5. 扩展点

- 新 OpCode 的渲染：在 Renderer 添加 handler，保持默认回退。
- 新样式需求：通过 StyleRegistry（按 `kind`）进行可选配置。
- 非阻塞动画：可引入调度器或 Qt Animation，但必须保持 Step 语义不变。

## 6. 当前限制（P0.6）

- 动画为同步阻塞插值，可能导致 UI 卡顿。
- 形状/配色硬编码，缺少皮肤系统。

> 交叉引用：Ops 协议见 `ops_spec.md`，Style/Metrics 约束见 `architecture.md` 第 7 节。
