---
bound_phase: P0.7
version: v0.7.18
status: Active
last_updated: 2025-12-24
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.7 — List + Tree Baseline（Model-First）
- Scope: 在 ListModel 全链路基础上，交付 BST/Tree 最小可用版本（create/insert/search/delete/delete_all），验证“按指令快速扩展”链路，为 AVL/Huffman 等树类模型打样。
- Completion highlights:
  - ListModel：create/insert/delete_index/delete_all/search/update（index/value 双模式）全链路 L2 微步骤 + 消息提示；sentinel 展示用，ID 使用 allocator；Dev hook 串联全操作，UI 冒烟测试覆盖。
  - BST：支持 create/insert/search/delete_value/delete_all；删除使用后继替换法并处理后继带右子；搜索/插入/删除的节点与边状态有统一恢复；消息锚点基于场景 bbox，靠近结构区域；Dev hook `_play_bst_full_demo` 覆盖命中/未命中搜索与三类删除。
  - Layout：SceneGraph 按 kind→策略路由（list→LINEAR，bst→TREE），为每个结构分配 `(dx, dy)` 偏移（按策略分组行累加）注入 LayoutEngine，避免多结构重叠；TreeLayout 注入 SET_POS。
  - SceneGraph/Schema：通过全局 registry 注册命令与 model factory，bst 无需硬编码；校验函数具名且统一抛 CommandError。
  - Tests：全量 `uv run pytest`、ruff/mypy 通过（授权访问 uv 缓存）；新增“后继带右子”回归用例覆盖重连逻辑。
- Active assumptions/limitations:
  - 动画仍为同步阻塞插值，未支持 seek/skip/倒播；后继遍历的恢复仍可细化，但不影响拓扑正确性。
  - Layout 分区为占位算法，偏移常量硬编码；消息锚点依赖场景 bbox，未按结构局部优化。
  - Renderer 无箭头/端点裁剪，边渐入渐出为整体插值；状态/颜色未配置化。
  - UI 为 Dev playground：单场景，无多 Timeline 管理；BST/DSL 入口为开发者菜单，未做正式用户流程。
  - DSL 仍是 JSON 占位，无变量/语法；LLM 仅接口，无外部调用。
  - Qt 测试依赖 `QT_QPA_PLATFORM=offscreen`；如需自定义 uv 缓存可设 `UV_CACHE_DIR=./tmp/uv-cache`。

### High-order issues (critical)
- 动画调度阻塞，缺少 skip/seek/倒播；Renderer/scene 仍单线程播放，复杂结构可能卡顿。
- 多结构视觉分区仍为常量偏移，未有容器/自动分区；消息锚点基于场景 bbox，未按结构定制。
- Renderer 样式/动画参数未配置化：无箭头、无端点裁剪，渐绘/缩回缺失；颜色/状态未集中规范。
- Layout stateful，缺少重放/重建接口，未来 seek/重排 timeline 受阻；DAG/多树布局策略缺位。
- DSL 仅 JSON 占位，无语法/变量/作用域；LLM 仅接口，无安全过滤；命令批量仍阻塞。
- UI 为 Dev playground，无正式播放控制、无多 Timeline 管理。
- 文档需持续同步：新增树类模型、消息锚点与布局偏移需在设计文档和 registry 中更新；未来 Agent 需要“全流程指南”作为默认入口。

## Completed Plan: Milestone 1 — Layout 抽象与策略化（兼容完成）
- 交付：LayoutEngine/reset + LayoutStrategy (LINEAR/TREE/DAG 占位)；SimpleLayout 实现接口并保留 LINEAR 默认；SceneGraph 兼容接入；文档/registry 同步。
- 测试：核心冒烟 + 全量 pytest/ruff/mypy 通过。
- TODO（P0.8）：布局策略路由、reset/seek 调用点、树/DAG 实现与无状态重建。

## Completed Plan: Milestone 2 — Renderer 配置化与消息策略
- 交付：RendererConfig（颜色、节点半径、max_frames、show_messages、easing 占位）注入 PySide6Renderer；默认视觉/阻塞播放保持；消息可禁用；UI 增加 Messages 开关；文档（renderer/animation/index）同步。
- 测试：属性/配置应用测试、UI 消息开关测试；全量 pytest/ruff/mypy 通过。
- TODO（P0.8）：非阻塞/seek/缓动真正实现；消息锚定/富提示；样式与 Layout 联动（尺寸/间距配置）。

## Completed Plan: Milestone 3 — 动画/状态规范文档化
- 交付：更新 `animation.md`（状态/颜色表、消息策略、配置占位说明），`model.md`（新模型开发指北模板、状态/消息/微步骤/测试建议），`index.md` 同步版本。
- 范围：仅文档，未改代码行为；保持与现状一致并标注未来项（锚定消息、非阻塞动画）。
- 测试：无代码改动，延用前次全量通过结果。


## Completed Plan: Milestone 4 — SceneGraph/command_schema 可维护性
- 交付：可读校验函数 + 统一 CommandError；注册 helper（register_command/register_model_factory）与全局 registry；SceneGraph 使用全局模型工厂，无硬编码；文档/registry 同步。
- 测试：命令校验/SceneGraph 路由测试 + 全量 pytest/ruff/mypy 通过。
- 当前进展：命名校验函数替换匿名 lambda，统一 CommandError；引入 register_command/register_model_factory，SCHEMA/MODEL_OP/MODEL_FACTORY registry 支持默认 list 注册；SceneGraph 使用全局工厂 registry，去除硬编码；相关测试通过，scene_graph 文档/index 同步。

## Completed Plan: Milestone 5 — DSL/LLM 入口 + Persistence
- 交付：
  - JSON Command 协议（导入/导出 + SCHEMA_REGISTRY 校验）：`persistence/json_io.py`。
  - DSL 占位：`dsl/parser.py` 接受 JSON 作为 DSL 输入；`dsl/cli.py` CLI 入口；UI Dev 菜单提供 DSL/JSON 输入并执行。
  - LLM 适配占位：`llm/adapter.py` 定义 `LLMClient` 协议与 `LLMAdapter`（前缀 + 可插拔 client，默认直通）。
  - 文档：新增 `docs/design/dsl.md` / `json.md` / `llm.md`，registry 同步。
- 测试：全量 pytest/ruff/mypy 通过（79/79），新增 CLI/LLM 测试覆盖。
- 假设/限制：
  - DSL 仍为 JSON 占位，无真实语法/语义检查；无变量/作用域。
  - 无外部 LLM 调用，未做安全过滤；仅提供接口。
  - 执行阻塞，批量命令可能卡 UI；无撤销/seek。
  - 未定义协议版本/流式导入，错误即抛。

## Active Plan: Milestone 6 — 树形模型起步（基础骨架）
- 目标：验证“按指令快速扩展”能力，交付 BST 最小可用全链路（Model/Schema/Layout/Renderer/UI Hook），为后续 AVL/Huffman/DAG 铺路。
- 进展：
  - BST 模型已支持 create/insert/search/delete_all/delete_value，删除后继带右子时正确重连；SceneGraph/Schema registry 化，无硬编码；Layout 路由与 per-structure 偏移避免多结构重叠；Dev UI `_play_bst_full_demo` 覆盖插入/查找/删除。
  - Renderer 消息锚点改为场景 bbox 顶部居中，方便观察；PySide6 renderer 仍阻塞播放，但冒烟通过。
- 待办 / 风险：
  - 动画可进一步细化：后继遍历的状态恢复、删除过程分步消息；边箭头/端点裁剪与渐绘待 P0.8。
  - Layout 分区仍为常量偏移，复杂混排（多树+线性+DAG）需后续引入自动分区/容器框。
  - UI 仍为 Dev hook，缺少正式用户流与播放控制（seek/skip）；DSL/LLM 未与树语义绑定。

## Planned Next Phase (Delayed): P0.8 — Renderer/Layout Responsiveness
- 状态：暂缓启动，等待 P0.7 收口及基线稳定后再排期。
- 方向（维持原设想，后续再细化）：非阻塞播放（seek/skip）、可配置缓动与消息展示优化；Layout 需支持重放/重建以解耦时序，Renderer 样式/尺寸配置化。
- 仍需扩展 BST/GitGraph 模型与命令注册，补充多结构容器/分区策略。
- 若提前启动的工作（如 Layout 抽象）需保持兼容 SimpleLayout 并可随时回滚。
### P0.8 子任务（Renderer 动画增强，待启动）
- 有向边视觉：箭头绘制 + 起终点从节点边界算起（复用 node_radius）。
- 边动画：CREATE_EDGE/DELETE_EDGE 支持端点插值式“渐绘/缩回”；配置开关可放在 RendererConfig。

## Upcoming: Milestone 7 — 全流程开发指南
- 目标：输出“从需求到交付”的可操作指南，确保新 Agent 可按模板快速扩展模型/命令/布局/渲染/UI/测试/文档。
- 内容占位：TDD 步骤、微步骤拆解与颜色/消息约定、SceneGraph/Schema 注册流程、Layout/Renderer 钩子、Dev/UI 验收、DSL/JSON 流程、CI 检查清单。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
