---
bound_phase: P0.6
version: v0.2
status: Draft
last_updated: 2025-12-15
---

# MODEL — 设计说明（轻量）

本文件描述 Model 层职责边界与扩展方式，避免实现细节耦合。

## 1. 角色与职责

- 维护真实数据结构状态（逻辑拓扑、值、关系）。
- 将操作拆解为结构 Ops（不含位置）。
- 保证 ID/EdgeKey 稳定（至少在结构生命周期内单调）。

## 2. 输入输出

- 输入：SceneGraph 传入的 model op + payload。
- 输出：`Timeline`（包含结构 Ops）。

## 3. 约束与边界

- **不得**依赖 Layout/Renderer/UI/SceneGraph 实现细节。
- **不得**输出 `SET_POS`（由 Layout 注入）。
- **不得**吞异常：逻辑错误抛 `ModelError`。
- **应**输出 `kind`，用于渲染/布局语义（见 ops_spec）。

## 4. 扩展点

- 新结构实现：继承 `BaseModel`，实现 `kind`/`node_count`/`apply_operation`。
- L2 动画：将高层操作拆解为多个 Step（Highlight → Structural → Restore 等）。

## 5. 推荐实现模式（可选）

为提升 L2 动画的可读性与复用性，建议使用“builder + step 编排 (emitter)”的轻量模式：

- **Builder 仅作为可选 helper**：例如 `_build_create_node_op`、`_build_create_edge_op`、`_add_state_step`。
- **不强制统一抽象**：无边结构（如 seqlist）可完全不使用 edge builder，仅使用节点/标签/状态 helper。
- **核心原则**：不引入跨层耦合，不要求所有模型遵循同一套 builder 类或基类。

该模式是推荐实践，不是协议或强制规范。

## 6. 当前限制（P0.6）

- 除 list 外的模型仍为空壳。
- list 模型并不完整，只有 insert 操作满足要求
- 可复用的 builder 库并未建立
- ID 稳定性策略仅在 list 完整落地。

> 交叉引用：Ops 语义见 `ops_spec.md`，架构边界见 `architecture.md`。
