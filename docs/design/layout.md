---
bound_phase: P0.7
version: v0.7.3
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

## 5. 当前实现（P0.7）

- **SimpleLayoutEngine (LINEAR)**：stateful 顺序引擎，固定尺寸与左对齐，按结构行堆叠；无 seek/倒播。
- **TreeLayoutEngine (占位 TREE)**：基于 CREATE_EDGE 的父子关系，中序遍历编号，水平等距、纵向分层；用于树模型冒烟（kind=bst/tree 预留）。
- SceneGraph 路由与分区：kind→LayoutStrategy（list/seqlist/stack→LINEAR，bst/huffman→TREE，git→DAG），每个结构分配 `(dx, dy)` 偏移（按策略分组、行累加；DAG 具备横向 lane 偏移）注入 LayoutEngine，避免多结构重叠；偏移为占位参数，可后续替换为配置化/分区算法。list 间距 120，seqlist 间距 80（矩形单元），stack 间距 80（竖向），huffman 队列间距默认 80。
- Per-kind 布局配置：LINEAR 引擎支持按结构注入 orientation/spacing/row_spacing/start_x/start_y（stack 默认 vertical；list/seqlist 默认 horizontal）；桶容器（bucket）通过 SET_POS 单独定位，vertical 时以节点 bbox 纵向居中。TreeLayout 支持 `queue_spacing/queue_start_y/tree_offset_y/tree_span`（Huffman 双区布局：队列根在上方横排，子树沿 `tree_offset_y` 向下展开）。

## 6. 即将扩展的布局需求（P0.8 计划）

- 顺序表（seqlist）/栈（stack）：已具备桶容器 + 矩形单元定位；后续需支持自动尺寸推导、容器 label/指针等增强。
- Huffman 构建：双区域布局（队列横排 + 树向下展开）已初版支持，队列根节点按 `queue_index` 排序定位，子树从根向下偏移；后续可细化子树水平压缩与动态队列尺寸。
- Git DAG：纵向 lane 占位布局（多列或单列），节点小圆点+标签，按时间/序号递增偏移；分支/merge 需要横向移位或平行 lane。
- 多结构分区：SceneGraph 需根据 kind 划分区域并传递 `(dx, dy)`，避免矩形桶与树/DAG 重叠；偏移应配置化而非魔数。

上述需求应通过 LayoutStrategy 扩展或参数化实现，保持“仅注入 SET_POS”，不得耦合 Renderer 细节。

## 7. 当前限制

- SimpleLayout 为 stateful 顺序引擎，固定尺寸与左对齐；不支持 seek/倒播。
- 多结构冲突处理有限：树/线性混排可能拥挤；无自动分区。
- 分区/偏移为固定常量，未暴露配置；未来需根据结构尺寸/布局策略自动分配。
- 无 seek/倒播/重建；布局状态依赖顺序执行。
- 树布局为占位算法，无平衡/重排动画，复杂树（旋转等）可能需要更精细算法。

> 交叉引用：Ops 语义见 `ops_spec.md`，Style/Metrics 约束见 `architecture.md` 第 7 节。
