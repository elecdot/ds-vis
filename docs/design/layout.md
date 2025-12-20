---
bound_phase: P0.6
version: v0.1
status: Draft
last_updated: 2025-12-15
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

## 3. 约束与边界

- **不得**修改结构 Ops（CREATE/DELETE 等）。
- **不得**依赖 Renderer 或 UI。
- **仅**注入 `SET_POS`。
- **应**消费 MetricsRegistry（按 `kind` 的尺寸/间距提示），缺省时回退默认值。

## 4. 扩展点

- 新布局策略：Tree/DAG/Linear 各自实现，SceneGraph/上层选择策略。
- 未来可支持布局重建以启用 seek/倒播。

## 5. 当前限制（P0.6）

- SimpleLayout 为 stateful 顺序引擎，固定尺寸与左对齐；不支持 seek/倒播。
- 多结构冲突处理有限，仅垂直堆叠。

> 交叉引用：Ops 语义见 `ops_spec.md`，Style/Metrics 约束见 `architecture.md` 第 7 节。
