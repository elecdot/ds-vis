---
bound_phase: P0.7
version: v0.5
status: Draft
last_updated: 2025-12-24
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
- 可复用的 builder 库仍为轻量 helper，未形成通用库。
- ID 稳定性策略仅在 list 落地，其他结构待补。

## 7. ListModel 实现备注（P0.7）

- 操作覆盖：create / insert / delete_index / delete_all / search（index/value）/ update（index/value），均输出 L2 微步骤。
- sentinel 仅用于展示空表：不计入 `_node_ids` / `node_count`，ID 通过 allocator 生成，空表插入前会删除 sentinel。
- 颜色语义：遍历类步骤使用 `secondary`，旧边（待重连）使用 `to_delete`，关键节点/新边使用 `highlight`。
- 消息提示：insert/search/update 会在步骤前后用 `SET_MESSAGE`，结束后 `CLEAR_MESSAGE`；消息位置由 Renderer 决定（当前为固定文本）。

## 8. 新模型开发指北（模板，P0.7）

- 状态/颜色：优先使用统一状态值（见 animation.md），避免自定义散乱命名。
- 微步骤拆解模板：遍历/定位（secondary）→ 关键节点/边高亮（highlight）→ 结构变更（CREATE/DELETE/SET_LABEL 等）→ 恢复（normal）。
- 消息：在操作开始/结果使用 `SET_MESSAGE`，完成后 `CLEAR_MESSAGE`；尊重 RendererConfig.show_messages。
- ID/边命名：使用 allocator，边 key 稳定（`structure_id|kind|src->dst`）；sentinel 仅展示。
- 测试建议：正/误路径，ID 稳定性，微步骤标签/状态覆盖；若复杂行为未实现可用 xfail 锁定预期。

> 交叉引用：Ops 语义见 `ops_spec.md`，架构边界见 `architecture.md`。

## 9. Tree/BST 骨架（P0.7 起步）
- 目标：提供 BST 风格的链式基础树骨架，为后续 AVL/Huffman 等复用。当前覆盖 create/insert，旋转/平衡留空。
- 实现要点：
  - kind=`tree`，注册 CREATE_STRUCTURE/INSERT/DELETE_STRUCTURE；payload 采用 `value` 插入，create 可批量按顺序 insert。
  - 结构状态：节点保存 key、左右子指针、parent；ID 使用 allocate_node_id 单调生成；边 key 使用 `edge_id(edge_kind, src, dst)`，edge_kind 为 `left`/`right`。
  - 微步骤：遍历路径设为 secondary，插入父节点设 highlight，CREATE_NODE/CREATE_EDGE 标记左右（label=L/R），末尾恢复状态 + CLEAR_MESSAGE。无 SET_POS，交由 Layout 注入（当前用线性占位，树形布局待后续）。
  - 删除：DELETE_STRUCTURE 走 delete_all，先删边再删节点，无 sentinel。
- 限制/待办：
  - 未实现 search/delete/旋转；未做平衡与重复键策略（当前重复键落右子树）。
  - 树形布局为占位（沿用 SimpleLayout 行堆叠），混排多结构时需后续分区/树布局策略。
  - DSL 仍为 JSON 占位，真实 DSL 语法需同步命令/校验。
