---
bound_phase: P0.7
version: v0.7.0
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

## Planned Next Phase: P0.8 — Renderer/Layout Responsiveness
- 方向：非阻塞播放（seek/skip）、可配置缓动与消息展示优化；Layout 需支持重放/重建以解耦时序，Renderer 样式/尺寸配置化。
- 仍需扩展 BST/GitGraph 模型与命令注册，补充多结构容器/分区策略。

## Invariants
- project_state.md is the only authority on current phase.
- Other docs must not restate "current status", only bind to phases.
