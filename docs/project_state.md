---
bound_phase: P0.7
version: v0.7.15
status: Active
last_updated: 2025-12-24
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.7 — ListModel Full Coverage (Model-First)
- Scope: ListModel 操作集补全（create/insert/delete/search/update/delete_all），L2 微步骤与消息提示，形成可复用的 builder+step 编排范式；提供 Dev 全链路验收 hook。
- Completion highlights:
  - ListModel 支持 create/insert/delete_index/delete_all/search/update（index/value 双模式），全链路 L2 微步骤 + 消息提示；sentinel 仅展示用，不计入逻辑节点，ID 走 allocator。
  - 颜色语义细化：遍历使用 secondary，旧边使用 to_delete，关键节点/新边用 highlight。
  - Dev hook `_play_list_full_demo` 串联全操作（含空表、头/中/尾插、search 命中/未命中、update、delete、clear），UI 冒烟测试覆盖。
  - 新增 CommandType.UPDATE，SceneGraph/command_schema 路由与校验齐备；核心测试、ruff/mypy 通过。
- Active assumptions/limitations:
  - 动画仍为同步阻塞插值，未支持 seek/skip/倒播；Renderer 配色/形状硬编码。
  - 结构覆盖面仍仅 list；其他模型为空壳，ID 稳定性未落地。
  - Layout 仍左对齐、固定尺寸、有状态顺序执行；缺少 Metrics/Style 配置。
  - UI 仍为 Dev playground：单场景，无多 Timeline 管理；message 仍为固定位置文本。
  - Qt 测试依赖 `QT_QPA_PLATFORM=offscreen`；命令需在项目根执行，uv 缓存可设置 `UV_CACHE_DIR=./tmp/uv-cache`。

### High-order issues (critical)
- 时间控制阻塞，缺少 skip/seek/倒播与非阻塞调度；性能/体验需迭代。
- 命令/模型覆盖面有限：仅 list；扩展 BST/GitGraph 需补注册表、模型与测试。
- 结构 ID 稳定性仅在 list 覆盖，其他结构仍为索引派生。
- 多结构视觉分区（结构容器框/区域分配）未落地，混排可能冲突。
- Layout stateful，缺少重放/重建接口，未来 seek/重排 timeline 受阻；多布局策略缺失（树/DAG 等）。
- Renderer 样式/动画参数未配置化，消息固定位置；缺少状态/颜色规范表，跨模型扩展易不一致。
- Dev 合并 timeline 依赖“预注入 SET_POS 的顺序播放”，若未来布局需重建/seek，需调整策略。
- DSL/LLM 入口与最小语法缺失，即便层次清晰，Agent 缺锚点。
- command_schema 验证用 lambda+抛异常技巧，可读性差，扩展时易踩坑。
- 设计文档阶段标记滞后（architecture/animation 等仍为 P0.6），需在后续同步新增命令/颜色语义/消息习惯。
- 测试盲区：BST/GitGraph 等模型仍为空壳且未在文档显式标记，容易误判已部分实现；需在扩展前明确状态与期望。

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
- 目标：验证“按指令快速扩展”能力，先落地一个链式存储的树模型最小集（可作为 BST/AVL/Huffman 的共用骨架），覆盖 create/insert 微步骤范式与命令注册。
- 范围：
  - Model：新增 Tree 基础模型（链式节点、左右子指针、ID/Edge key 策略、L2 微步骤模板）。
  - SceneGraph/Schema：注册树类命令路由与校验（至少 create/insert，占位旋转/平衡可暂存 xfail）。
  - Layout：简单树形坐标占位（可用静态层次或复用 SimpleLayout 变体，确保与线性结构不冲突），必要时标注 TODO。
  - Renderer/UI/Dev：最小冒烟 Hook（Dev 菜单或 CLI 回放）验证全链路。
- 验收：模型/SceneGraph/命令校验测试；可视化冒烟（基础节点/边呈现）；全量 CI 通过；文档/registry 同步。
- 风险/假设：
  - 树形 Layout 选择与多结构混排：需避免与线性布局重叠，可能需临时固定原点或分区策略占位。
  - 非阻塞动画缺失，复杂树操作（旋转）可能卡顿；旋转可先以占位/xfail 锁定预期。
  - 仅做最小骨架，后续 AVL 旋转/平衡逻辑、真实 DSL 语法仍需迭代。
- 当前进展：已落地 tree 基础模型（create/insert/delete_all）、注册命令/工厂、SceneGraph 流程与 UI/CLI 冒烟测试通过；增加 TreeLayoutEngine（中序层次占位）并在 SceneGraph 中按 kind=tree 路由，仍为占位算法，混排分区待后续。

## Planned Next Phase (Delayed): P0.8 — Renderer/Layout Responsiveness
- 状态：暂缓启动，等待 P0.7 收口及基线稳定后再排期。
- 方向（维持原设想，后续再细化）：非阻塞播放（seek/skip）、可配置缓动与消息展示优化；Layout 需支持重放/重建以解耦时序，Renderer 样式/尺寸配置化。
- 仍需扩展 BST/GitGraph 模型与命令注册，补充多结构容器/分区策略。
- 若提前启动的工作（如 Layout 抽象）需保持兼容 SimpleLayout 并可随时回滚。
### P0.8 子任务（Renderer 动画增强，待启动）
- 有向边视觉：箭头绘制 + 起终点从节点边界算起（复用 node_radius）。
- 边动画：CREATE_EDGE/DELETE_EDGE 支持端点插值式“渐绘/缩回”；配置开关可放在 RendererConfig。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
