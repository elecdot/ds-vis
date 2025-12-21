---
bound_phase: P0.7
version: v0.2
status: Draft
last_updated: 2025-12-24
---

# SCENE_GRAPH — 设计说明（轻量）

本文件仅描述 **SceneGraph** 的职责边界、输入输出与扩展点，避免实现细节耦合。
若需新增命令/模型/布局策略，请优先参考本文件与 `architecture.md`。

## 1. 角色与职责

- 维护场景中所有结构实例的生命周期（按 `structure_id` 管理）。
- 接收 `Command` 并做 schema 校验、路由到 Model 操作。
- 将 Model 输出的结构 Ops 交给 Layout 注入 `SET_POS`（通过 `LayoutEngine` 接口，默认 SimpleLayout/LINEAR 策略），再交 Renderer 播放。
- 提供可序列化的结构状态（供 persistence 使用，后续阶段实现）。

## 2. 输入输出

- 输入：`Command`（结构 ID、类型、payload）。
- 输出：`Timeline`（多个 `AnimationStep`）。

## 3. 约束与边界

- **不得**直接访问 Model 内部状态，必须通过 `BaseModel` 公共接口。
- **不得**依赖 Renderer / UI / DSL 的实现细节。
- **必须**遵循 schema/映射注册表，未知命令需抛 `CommandError`。

## 4. 扩展点

### 4.1 新增命令
- 在 `command_schema.py` 中添加 schema。
- 在 `MODEL_OP_REGISTRY` 中映射到 Model 操作名。
- 在 SceneGraph handler 中路由到对应操作，保持校验与错误一致。

### 4.2 新增模型
- 新 Model 需实现 `BaseModel`（`kind`/`node_count`/`apply_operation`）。
- 在 `_model_registry` 注册 `(kind, kind) -> factory`。
- 必须生成结构 Ops（CREATE/DELETE/SET_STATE/SET_LABEL 等），不生成布局信息。

## 5. 错误处理

- 校验失败：抛 `CommandError`。
- Model 抛 `ModelError` 时：SceneGraph 透传或转为 `SceneError`。
- 上层（UI/DSL）负责兜底展示。

## 6. 当前限制（P0.6）

- 当前命令覆盖 list：CREATE_STRUCTURE / DELETE_STRUCTURE / DELETE_NODE / INSERT / SEARCH / UPDATE。
- 未实现 persistence 的导入导出。
- 暂无 seek/倒播，需要 Layout/Renderer 支持状态重建后再扩展。

> 交叉引用：命令/校验规范见 `command_schema.py`，架构边界见 `architecture.md`。
