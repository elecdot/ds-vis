---
bound_phase: P0.7
version: v0.1
status: Draft
last_updated: 2025-12-24
---

# 全流程开发指南（Agent 快速上手）

目标：帮助新 Agent 从需求到交付快速落地一个结构/命令（以 BST/List 经验为模板），覆盖 Model → Layout → SceneGraph → Renderer/UI → 测试 → 文档。

## 快速路径（步骤清单）
1) **对齐需求与范式**
   - 查阅 `project_state.md`、`animation.md`、`model.md`，确认状态/颜色/消息范式与当前限制。
   - 明确操作集合与微步骤粒度（教学级 L2：比较/决策/移动/重连/恢复）。
2) **先写测试（TDD）**
   - 覆盖：正/误输入、ID/边稳定性、状态/消息关键断言、边界案例。
   - 如果功能未实现，用 `xfail` 锁定预期。
3) **注册命令与模型**
   - 在 `command_schema.py` 用 `register_command` 注册 CommandType + kind → schema + model_op。
   - 若新 kind：用 `register_model_factory` 注册工厂，避免 SceneGraph 硬编码。
4) **实现 Model**
   - `kind`/`apply_operation`/ID 与 edge key 稳定；生成结构 Ops（不含 SET_POS）。
   - 按 `animation.md` 拆微步骤：路径 secondary，高亮关键节点/边，结束统一 Restore + CLEAR_MESSAGE。
   - 删除/重连要同步内存拓扑与 Ops（先删旧边，再重连，再删节点）。
5) **接入 Layout**
   - 确认 SceneGraph 中 kind→LayoutStrategy 路由（LINEAR/TREE/DAG 占位）和 per-structure `(dx, dy)` 偏移。
   - 若需新策略，扩展 LayoutEngine 并更新路由；确保不与现有结构重叠。
6) **Renderer/UI/Dev Hook**
   - PySide6Renderer：遵循状态/消息语义；消息当前锚定场景 bbox 顶部。
   - UI：添加 Dev 菜单冒烟 Hook（create/insert/search/delete 等串联），便于人工验收。
7) **DSL/JSON/LLM 接口**
   - JSON：确保 Command schema 往返；dsl/parser 目前接受 JSON 占位。
   - LLM：接口在 `llm/adapter.py`，按需扩展 prompt/客户端，但保持可选。
8) **验证与提交**
   - 运行 `uv run ruff check`, `uv run mypy src`, `uv run pytest`（必要时设置 `UV_CACHE_DIR`）。
   - 更新文档：`project_state.md`（状态/里程碑）、`index.md`（版本表）、相关设计文档（animation/model/layout/scene_graph/renderer）、如有新增指南/DSL/JSON/LLM 补充对应文件。
   - 检查前置元数据（front matter）与 registry 版本一致。

## 常见坑位与防御
- **状态恢复遗留**：查找/删除路径的节点与边需在末尾恢复 normal，消息需 CLEAR。
- **拓扑同步**：DELETE/重连需同时更新内存 parent/child 指针与 Ops，避免渲染残留。
- **布局混排**：多结构共存时注意偏移/分区，避免 SET_POS 冲突；必要时标注 TODO。
- **阻塞动画**：长链/大树会卡 UI，控制 `duration_ms` / `max_frames`，关键冒烟测试可减速但保持覆盖。
- **文档版本**：忘记同步 `index.md` / front matter 会导致后续 Agent 误判状态。
