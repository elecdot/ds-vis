---
bound_phase: P0.7
version: v0.7.20
status: Active
last_updated: 2025-12-22
---

# Project State — Single Source of Truth

This document captures the active delivery phase, what is complete, current assumptions/limitations, and the next planned phase. It is the canonical status reference (SSOT) and should stay minimal.

## Active Phase: P0.7 — List + Tree Baseline（Model-First）
- Scope: 在 ListModel 全链路基础上，交付 BST/Tree 最小可用版本（create/insert/search/delete/delete_all），验证“按指令快速扩展”链路，为 AVL/Huffman 等树类模型打样。
- Completion highlights:
  - ListModel：create/insert/delete_index/delete_all/search/update（index/value 双模式）全链路 L2 微步骤 + 消息提示；sentinel 展示用，ID 使用 allocator；Dev hook 串联全操作，UI 冒烟测试覆盖。
  - BST：支持 create/insert/search/delete_value/delete_all；删除使用后继替换法并处理后继带右子；搜索/插入/删除的节点与边状态有统一恢复；消息锚点基于场景 bbox，靠近结构区域；Dev hook `_play_bst_full_demo` 覆盖命中/未命中搜索与三类删除，动画已通过当前验收（仍需关注后继遍历恢复、消息拆分等细化项）。
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
- 历史里程碑已移出此文档，需查阅设计文档或 `docs/PLAN.md`。

### High-order issues (critical)
- 动画调度阻塞，缺少 skip/seek/倒播；Renderer/scene 仍单线程播放，复杂结构可能卡顿。
- 多结构视觉分区仍为常量偏移，未有容器/自动分区；消息锚点基于场景 bbox，未按结构定制。
- Renderer 样式/动画参数未配置化：无箭头、无端点裁剪，渐绘/缩回缺失；颜色/状态未集中规范。
- Layout stateful，缺少重放/重建接口，未来 seek/重排 timeline 受阻；DAG/多树布局策略缺位。
- DSL 仅 JSON 占位，无语法/变量/作用域；LLM 仅接口，无安全过滤；命令批量仍阻塞。
- UI 为 Dev playground，无正式播放控制、无多 Timeline 管理。
- 文档需持续同步：新增树类模型、消息锚点与布局偏移需在设计文档和 registry 中更新；未来 Agent 需要“全流程指南”作为默认入口。

## Planned Next Phase — 快速可交付（P0.8 候选）
- 目标：在 BST/List 验收基线上，进一步提升课堂演示可用性与冒烟效率，同时保持现有阻塞渲染兼容。
- 交付重点（按优先级）：
  1) Renderer/消息体验：在阻塞模式下增加“加速/跳过消息”配置入口，调整消息锚点以减少遮挡（按结构 bbox 或预留边距），并补充 show_messages/消息定位的 renderer 层测试。
  2) 稳定性回归：针对 BST 删除（含后继带右子）与搜索 miss 的状态恢复、消息拆分编写回归测试并修复；确保尾部统一恢复节点/边状态。
  3) Layout/UI 冒烟：复核 SceneGraph 偏移常量，避免多结构重叠；在 Dev 菜单补充多结构+BST 串联冒烟入口以缩短人工验收路径。
- 风险/边界：非阻塞播放、自动分区布局、样式配置化仍不在本轮范围，需与 SimpleLayout/阻塞渲染保持兼容。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
