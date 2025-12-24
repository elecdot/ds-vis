---
bound_phase: P0.7
version: v0.6.1
status: Active
last_updated: 2025-12-24
---

# SCENE_GRAPH — 设计说明

本文件描述 **SceneGraph** 的职责边界、指令解析逻辑与扩展点。

## 1. 角色与职责
- **生命周期管理**：维护场景中所有结构实例（按 `structure_id` 管理）。
- **指令分发**：接收 `Command`，执行 Late-binding 类型解析，并路由到 Model。
- **流水线串联**：Model (结构 Ops) -> Layout (位置 Ops) -> Renderer (播放)。
- **状态导出**：提供当前场景所有结构的指令序列，支持持久化。

## 2. 指令解析与 Late-binding (v0.6.1)
为了支持 DSL 的灵活性，SceneGraph 实现了延迟类型绑定：
- **自动补全 kind**：如果 `Command.payload` 中缺少 `kind` 字段，SceneGraph 会尝试从已存在的结构中查找该 ID 对应的类型并自动补全。
- **校验时机**：在补全 `kind` 后，SceneGraph 会调用 `SCHEMA_REGISTRY` 进行严格的字段校验。
- **创建约束**：`CREATE_STRUCTURE` 指令必须显式提供 `kind`。

## 3. 布局路由与分区
- **策略路由**：根据 `kind` 自动选择布局策略（如 `list -> LINEAR`, `bst -> TREE`）。
- **自动偏移**：为每个结构分配 `(dx, dy)` 偏移，防止多个结构在场景中重叠。

## 4. 扩展点
- **新增模型**：实现 `BaseModel` 并通过 `register_model_factory` 注册。
- **新增命令**：在 `command_schema.py` 中注册 `CommandType + kind` 的映射。

## 5. 错误处理
- **CommandError**：校验失败或指令非法时抛出。
- **ModelError**：模型逻辑错误（如空栈弹出）时抛出，由 UI 捕获并展示。
