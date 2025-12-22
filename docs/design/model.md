---
bound_phase: P0.7
version: v0.8.3
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

## 6. 当前限制（P0.7）

- 可复用的 builder 库仍为轻量 helper，未形成强制共用抽象（动画细化需按模型自定义）。
- ID 稳定性策略已用于 list/bst，其他模型待补；跨模型统一 allocator 策略仍需评估。
- 非阻塞/seek 未落地，模型侧缺少重放/重建接口（需与 Layout/Renderer 协同）。

## 7. ListModel 实现备注（P0.7）

- 操作覆盖：create / insert / delete_index / delete_all / search（index/value）/ update（index/value），均输出 L2 微步骤。
- sentinel 仅用于展示空表：不计入 `_node_ids` / `node_count`，ID 通过 allocator 生成，空表插入前会删除 sentinel。
- 颜色语义：遍历类步骤使用 `secondary`，旧边（待重连）使用 `to_delete`，关键节点/新边使用 `highlight`。
- 消息提示：insert/search/update 在步骤前后用 `SET_MESSAGE`，结束后 `CLEAR_MESSAGE`；PySide6 Renderer 将消息锚定场景 bbox 顶部居中。

## 8. SeqlistModel 实现备注（P0.8）
- kind=`seqlist`，顺序表（无边）；操作：create/insert/delete_index/delete_all/search/update。
- 微步骤：消息提示 → 目标/区间高亮（highlight/secondary）→ 结构变更（CREATE_NODE/DELETE_NODE/SET_LABEL）→ 统一 Restore（CLEAR_MESSAGE+SET_STATE normal）。
- ID 稳定：节点用 allocator 单调生成；不复用旧 ID。
- 视觉与布局：矩形单元 + 桶容器，布局由 SceneGraph 路由 LINEAR（horizontal）注入 SET_POS。
- 异常：参数缺失或越界抛 ModelError。

## 9. StackModel 实现备注（P0.8）
- kind=`stack`，栈（无边）；操作：create/push/pop/delete_all/search（线性扫描，教学可视化）。
- 顺序：内部 `values`/`_node_ids` 按 **top→bottom** 存储，create 将输入视为 push 序列（最后一个为栈顶）。
- 微步骤：Push=消息+桶高亮→CREATE_NODE→容器 resize→Restore；Pop=高亮栈顶→DELETE_NODE→容器 resize→Restore；Search=自顶向下高亮/secondary 标记；所有步骤结尾 CLEAR_MESSAGE + 状态恢复。
- 视觉与布局：矩形单元 + 桶容器，LINEAR 纵向布局（orientation=vertical，spacing≈80），桶位置按节点 bbox 纵向居中。
- 异常：push/pop 仅接受 index=0 或省略；参数缺失抛 ModelError。

## 10. HuffmanModel 实现备注（P0.8）
- kind=`huffman`；操作：build（输入权值列表）/delete_all。
- 逻辑：使用小顶堆维护候选队列，每轮取最小两节点生成父节点（权值相加），父节点入堆；最终根为 Huffman 树根。
- 微步骤：高亮两最小 → 创建父节点与两条边（L/R）→ 按权值重新入队并更新 queue_index → CLEAR_MESSAGE；完成后突出根节点。
- 视觉与布局：节点默认 circle，利用 `queue_index` 标注队列顺序；TreeLayout 支持 `queue_spacing/queue_start_y/tree_offset_y/tree_span` 将队列根横排、子树向下展开。
- 异常：权值需为数字；无数据时提示消息。

## 11. 新模型开发指北（模板，P0.7）

- 状态/颜色：优先使用统一状态值（见 animation.md），避免自定义散乱命名。
- 微步骤拆解模板：遍历/定位（secondary）→ 关键节点/边高亮（highlight）→ 结构变更（CREATE/DELETE/SET_LABEL 等）→ 恢复（normal）。
- 消息：在操作开始/结果使用 `SET_MESSAGE`，完成后 `CLEAR_MESSAGE`；尊重 RendererConfig.show_messages。
- ID/边命名：使用 allocator，边 key 稳定（`structure_id|kind|src->dst`）；sentinel 仅展示。
- 测试建议：正/误路径，ID 稳定性，微步骤标签/状态覆盖；若复杂行为未实现可用 xfail 锁定预期。

> 交叉引用：Ops 语义见 `ops_spec.md`，架构边界见 `architecture.md`。

## 12. BST 实现备注（P0.7）
- 目标：树类模型的首个可交付版本，为 AVL/Huffman 等复用微步骤范式与注册方式。
- 实现要点：
  - kind=`bst`，支持 create/insert/search/delete_value/delete_all；重复键策略：走右子树。
  - 状态：节点存 key/left/right/parent；ID 单调；边 key `edge_id(edge_kind, src, dst)`（edge_kind=`left`/`right`）。
  - 微步骤：查找/插入/删除路径节点高亮，边用 secondary；删除双子树使用后继替换法，重连边后删除后继，统一 Restore 状态；消息在步骤开头提示、结尾清空。
  - Layout/Pos：不直接生成 SET_POS，由 SceneGraph 路由到 TreeLayout 并注入偏移。
- 限制/待办：
  - 后继遍历/删除可进一步分步提示；旋转/平衡未实现（AVL/红黑树留待后续）。
  - 混排分区为常量偏移，树尺寸未参与计算；箭头/端点裁剪与渐绘依赖 Renderer P0.8。
  - DSL 仍为 JSON 占位，未绑定树语义；Git/Huffman/DAG kind 预留未实现。
