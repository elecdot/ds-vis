---
bound_phase: P0.7
version: v0.7.31
status: Active
last_updated: 2025-12-24
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.7 — List + Tree Baseline（Model-First）
- Scope: 在 ListModel 全链路基础上，交付 BST/Tree 最小可用版本（create/insert/search/delete/delete_all），验证“按指令快速扩展”链路，为 AVL/Huffman 等树类模型打样。
- Completion highlights:
  - ListModel：create/insert/delete_index/delete_all/search/update（index/value 双模式）全链路 L2 微步骤 + 消息提示；sentinel 展示用，ID 使用 allocator；Dev hook 串联全操作，UI 冒烟测试覆盖。
  - SeqlistModel：支持 create/insert/delete_index/delete_all/search/update，矩形节点 + 桶容器（专用 LINEAR 布局），消息+状态 L2 微步骤；命令注册/SceneGraph 路由/控制面板操作可用，模型/UI 测试覆盖。
  - StackModel：create/push/pop/delete_all/search（线性扫描）全链路，栈顶在 index0（top→bottom 顺序），矩形单元 + 桶容器（LINEAR 竖向、容器按节点 bbox 居中）；命令注册/SceneGraph 路由/UI push/pop 可用，模型/布局/UI 测试覆盖。
  - Huffman（进行中）：新增 HuffmanModel（build/delete_all），小顶堆驱动 L2 微步骤（选两最小→建父→重排队列），TreeLayout 支持 queue_index 双区布局（队列横排 + 子树向下展开）；schema/SceneGraph 注册、UI kind 添加，模型/布局/SceneGraph 测试覆盖，完整 UI/渲染体验待后续验收。
  - BST：支持 create/insert/search/delete_value/delete_all；删除使用后继替换法并处理后继带右子；搜索/插入/删除的节点与边状态有统一恢复；消息锚点基于场景 bbox，靠近结构区域；Dev hook `_play_bst_full_demo` 覆盖命中/未命中搜索与三类删除，动画已通过当前验收（仍需关注后继遍历恢复、消息拆分等细化项）。
  - Layout：SceneGraph 按 kind→策略路由（list→LINEAR，bst→TREE），为每个结构分配 `(dx, dy)` 偏移（按策略分组行累加）注入 LayoutEngine，避免多结构重叠；TreeLayout 注入 SET_POS。
  - SceneGraph/Schema：通过全局 registry 注册命令与 model factory，bst 无需硬编码；校验函数具名且统一抛 CommandError。
  - Tests：全量 `uv run pytest`、ruff/mypy 通过（授权访问 uv 缓存）；新增“后继带右子”回归用例覆盖重连逻辑。
- Active assumptions/limitations:
  - 动画仍为同步阻塞插值，未支持 seek/skip/倒播；后继遍历的恢复仍可细化，但不影响拓扑正确性。
  - Layout 分区为占位算法，偏移常量硬编码；消息锚点依赖场景 bbox，未按结构局部优化。
  - Renderer 无箭头/端点裁剪，边渐入渐出为整体插值；状态/颜色未配置化。
  - Renderer/布局暂缺特定形状与容器：顺序表/栈的“桶+矩形单元”、Huffman 构建过程的双区域（队列+树区）、Git DAG 纵向 lane 布局均未落地。
  - UI 为 Dev playground：单场景，无多 Timeline 管理；BST/DSL 入口为开发者菜单，未做正式用户流程。
  - DSL 仍是 JSON 占位，无变量/语法；LLM 仅接口，无外部调用。
  - Qt 测试依赖 `QT_QPA_PLATFORM=offscreen`；如需自定义 uv 缓存可设 `UV_CACHE_DIR=./tmp/uv-cache`。
- 历史里程碑已移出此文档，需查阅设计文档或 `docs/PLAN.md`。

### High-order issues (critical)
- 动画调度阻塞，缺少 skip/seek/倒播；Renderer/scene 仍单线程播放，复杂结构可能卡顿。
- 多结构视觉分区仍为常量偏移，未有容器/自动分区；消息锚点基于场景 bbox，未按结构定制。
- Renderer 样式/动画参数未配置化：无箭头、无端点裁剪，渐绘/缩回缺失；颜色/状态未集中规范。
- Layout stateful，缺少重放/重建接口，未来 seek/重排 timeline 受阻；DAG/多树布局策略缺位。
- DSL 仅 JSON 占位，无语法/变量/作用域；LLM 仅接口，无安全过滤；命令批量仍阻塞。
- UI 为 Dev playground，无正式播放控制、无多 Timeline 管理。
- 文档需持续同步：新增树类模型、消息锚点与布局偏移需在设计文档和 registry 中更新；未来 Agent 需要“全流程指南”作为默认入口。

## Planned Next Phase — v0.1 / v0.2 交付路线（快速迭代）
- 目标：完成 v0.1 全部必做（顺序表/栈/Huffman/Git DAG 基础/持久化）并推进 v0.2 核心（AVL、DSL 文本、Git 扩展、多结构场景、回放），每轮原子可审查。

### 迭代评估与后续规划

| 迭代编号 | 目标内容 | 执行与交付情况 | 后续迭代问题/待办 |
| :--- | :--- | :--- | :--- |
| **迭代 L** | **布局架构重构** | **启动中**。针对树重叠、拓扑嗅探脆弱性、个性化布局缺失进行大修。 | 1. 定义 `Layoutable` 协议；2. 实现无状态布局计算；3. 引入 Buchheim 树算法。 |
| **迭代 0** | 基线巩固 (BST) | **部分交付**。BST 增删改查逻辑已通，回归测试覆盖了后继带右子场景。 | 1. 消息拆分需更细粒度（教学向）；2. 复杂删除后的状态恢复（高亮残留）需进一步验证。 |
| **迭代 1** | 顺序表 Seqlist | **已交付**。模型、LINEAR 布局、桶容器渲染、Dev Hook 全链路打通。 | 无（转入维护）。 |
| **迭代 3** | Huffman 构建 | **部分交付**。模型逻辑与双区布局（队列+树）已落地，SceneGraph 已注册。 | 1. **严重**：树布局存在节点重叠；2. 构建过程的渲染平滑度需优化。 |
| **迭代 4** | Git DAG 基础 | **部分交付**。`init`/`commit`/`checkout` 逻辑已通，支持基础 DAG 布局。 | 1. Lane 布局算法需优化以支持复杂分支；2. 分支/HEAD 标签的视觉区分度增强。 |
| **迭代 P** | Persistence | **进行中 (Stub)**。UI 按钮已预留，`json_io.py` 结构已搭建。 | 1. 实现所有已交付模型的序列化/反序列化逻辑；2. 打通 SceneGraph 的全量导入导出。 |
| **迭代 U** | UI/UX 交付化 | **进行中 (Playground)**。Dev 菜单可用，基础渲染器支持多状态。 | 1. 实现正式左侧控制面板；2. 消息锚点由全局改为按结构局部优化；3. 自动分区布局算法。 |
| **迭代 5** | DSL 文本 | **待启动**。目前仅为 JSON 占位。 | 1. 设计并实现最小 DSL 语法解析器；2. 接入 UI 输入框。 |
| **迭代 6** | v0.2 扩展 | **待启动**。 | 1. AVL 旋转动画；2. 动画历史回放功能。 |

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
