---
bound_phase: P0.7
version: v0.2
status: Draft
last_updated: 2025-12-24
---

# LAYOUT — 设计说明（轻量）

本文件描述 Layout 的职责边界与扩展方式，避免实现细节耦合。

## 1. 角色与职责

- 理解结构 Ops 推断拓扑信息。
- 计算几何布局并注入 `SET_POS`。
- 保障不同结构间的可视分布（当前仅线性堆叠）。

## 2. 输入输出

- 输入：结构 Ops（Timeline）。
- 输出：结构 Ops + `SET_POS` 注入后的 Timeline。
- 可选：提供 `reset()` / 重建入口以支持 seek/倒播或状态重放。

## 3. 约束与边界

- **不得**修改结构 Ops（CREATE/DELETE 等）。
- **不得**依赖 Renderer 或 UI。
- **仅**注入 `SET_POS`。
- **应**消费 MetricsRegistry（按 `kind` 的尺寸/间距提示），缺省时回退默认值。
- **应**提供清理接口 `reset()`（或同等能力）以便场景切换/重放。

## 4. 接口与扩展

- 接口：`LayoutEngine.apply_layout(timeline) -> Timeline`；可选 `reset()` 清理内部状态。
- 策略：`LayoutStrategy` 枚举（LINEAR/TREE/DAG），用于上层选择布局实现。
- 兼容：默认 SimpleLayout 作为 LINEAR 策略实现，保持 stateful 顺序行为。
- 扩展：Tree/DAG 布局可作为占位实现接入；重建/无状态模式可在未来支持 seek/倒播。

## 5. 当前限制（P0.6）

- SimpleLayout 为 stateful 顺序引擎，固定尺寸与左对齐；不支持 seek/倒播。
- 多结构冲突处理有限，仅垂直堆叠。

> 交叉引用：Ops 语义见 `ops_spec.md`，Style/Metrics 约束见 `architecture.md` 第 7 节。
