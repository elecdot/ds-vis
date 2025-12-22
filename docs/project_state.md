---
bound_phase: P0.7
version: v0.7.27
status: Active
last_updated: 2025-12-22
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.7 — List + Tree Baseline（Model-First）
- Scope: 在 ListModel 全链路基础上，交付 BST/Tree 最小可用版本（create/insert/search/delete/delete_all），验证“按指令快速扩展”链路，为 AVL/Huffman 等树类模型打样。
- Completion highlights:
  - ListModel：create/insert/delete_index/delete_all/search/update（index/value 双模式）全链路 L2 微步骤 + 消息提示；sentinel 展示用，ID 使用 allocator；Dev hook 串联全操作，UI 冒烟测试覆盖。
  - SeqlistModel：支持 create/insert/delete_index/delete_all/search/update，矩形节点 + 桶容器（专用 LINEAR 布局），消息+状态 L2 微步骤；命令注册/SceneGraph 路由/控制面板操作可用，模型/UI 测试覆盖。
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
- 目标：完成 v0.1 全部必做（顺序表/栈/Huffman/Git DAG 基础/持久化）并推进 v0.2 核心（AVL、DSL 文本、Git 扩展、多结构场景、回放），每轮原子可审查，遵循 PR checklist（ruff/mypy/pytest + 文档/registry 同步）。
- 迭代 0：基线巩固
  - BST 删除（含后继带右子）/搜索 miss 的状态恢复与消息拆分回归测试与修复；验证现有 List/BST 链路稳定性。
- 迭代 U：UI/UX 交付化
  - 设计并实现可交付 UI：左侧控制面板（结构选择/参数输入/播放控制/导入导出/DSL 输入）、右侧画布多结构偏移区、消息区防遮挡；接入各模型的快速操作入口。
  - Renderer/布局支持各模型视觉：顺序表/栈的“桶+矩形单元”（栈竖向）、Huffman 构建的队列区+树区、Git DAG 的纵向 lane、小圆节点/label；新增 UI 冒烟测试（offscreen）。
- 迭代 P：Persistence（v0.1）
  - 统一结构状态的 JSON 导入/导出（list/stack/bst/huffman/git），按 SCHEMA_REGISTRY 校验；UI 入口已提供 Import/Export 按钮（导入执行命令；导出当前为占位空列表）；persistence/控制面板冒烟测试通过；文件读写错误抛 CommandError。
- 迭代 1：顺序表 Seqlist（v0.1）
  - 实现模型（create/insert/delete/update/search）与命令注册；专用 LINEAR+桶布局，矩形单元渲染；Dev/UI hook 与动画/恢复测试；更新 model/layout/renderer 文档。
- 迭代 2：栈 Stack（v0.1）
  - 模型（create/push/pop）与命令注册；竖向桶布局（顶部指针）、矩形单元渲染；Dev/UI hook 与动画测试；同步文档。
- 迭代 3：Huffman 构建（v0.1）
  - 构建微步骤（优先队列展示 + 合并），自定义双区布局（队列横排 + 树区渐成），适配渲染；Dev/UI hook 与测试；更新 animation/model/layout 文档。
- 迭代 4：Git DAG 基础（v0.1）
  - 完成 init/commit/checkout（分支/commit）、HEAD/branch label 更新；DAG lane 布局与节点/label 渲染；持久化当前状态导出；UI/DSL 入口与冒烟测试。
- 迭代 5：DSL 文本 & 多结构场景（v0.2 部分）
  - 设计最小 DSL 文本语法 → Command 序列（覆盖 list/stack/bst/git 操作），CLI/Dev 输入；SceneGraph 多结构偏移校验与测试；文档同步。
- 迭代 6：v0.2 扩展与回放
  - AVL 平衡检测与 LL/RR/LR/RL 旋转动画；Git branch/merge（无冲突）+ DSL 脚本回放；持久化动画历史并支持阻塞回放；补充测试与文档。
- 风险/边界：非阻塞播放、自动分区布局、样式配置化仍不在本轮范围；`.git` 真实仓库解析可用占位/子集导入说明，需保持与现有阻塞渲染兼容。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
