---
bound_phase: P0.7
version: v0.2
status: Draft
last_updated: 2025-12-24
---

# 全流程开发指南（Agent 快速上手）

目标：帮助新 Agent 从需求到交付快速落地一个结构/命令（以 BST/List 经验为模板），覆盖 Model → Layout → SceneGraph → Renderer/UI → 测试 → 文档。

## 必读清单与技能
- **必读文档**：`AGENTS.md`（角色/红线）、`project_state.md`（当前阶段与限制）、`index.md`（版本表）、`animation.md`（状态/微步骤范式）、`model.md`、`layout.md`、`scene_graph.md`、`renderer.md`、`dev_kb.md`（已知问题/测试开关）。
- **工具技能**：`uv`（安装/运行）、pytest/ruff/mypy、`rg`（搜索）、PySide6 offscreen 测试（环境变量 `QT_QPA_PLATFORM=offscreen` 已在测试中使用）。
- **心智模型**：三层分离（Model→Layout→Renderer），跨层只用 Ops；SceneGraph 为唯一入口，命令必须校验。

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

## 详细流程（带检查点）
- **需求拆解**：把操作拆成微步骤列表（L2）；标记每步的状态值和消息文案。
- **Schema 注册**：新增命令/模型前，先在 `command_schema.py` 注册 schema 和 factory，跑 `tests/core/test_command_validation.py`。
- **Model 实现**：
  - ID/边 key 稳定（用 allocator；边用 `edge_id(kind, src, dst)`）。
  - 操作流程：定位路径 → 标记状态/消息 → 结构改动（创建/删除/重连/改 label）→ Restore（节点/边/消息）。
  - 内存拓扑与 Ops 同步：删边前断指针，重连后写 parent/child，最后删节点。
- **Layout 接入**：
  - 确认 kind 路由与偏移；若新增策略需补 LayoutEngine 并在 SceneGraph 注册。
  - 避免重叠：同策略多结构要叠加偏移；必要时在文档标注 TODO。
- **Renderer/UI**：
  - 消息锚点当前用场景 bbox 顶部；如需变更请同步 renderer 文档。
  - Dev Hook：在 UI Dev 菜单添加串联命令，便于冒烟；保持 duration 适中（关键动画可短）。
- **DSL/JSON/LLM**：保持 JSON 协议兼容；DSL 仍是占位，勿混用真实语法；LLM 仅接口。
- **文档同步**：代码变更涉及协议/流程时，更新设计文档 + `index.md` 版本号 + `project_state.md` 阶段说明。

## 常见坑位与防御
- **状态恢复遗留**：查找/删除路径的节点与边需在末尾恢复 normal，消息需 CLEAR。
- **拓扑同步**：DELETE/重连需同时更新内存 parent/child 指针与 Ops，避免渲染残留。
- **布局混排**：多结构共存时注意偏移/分区，避免 SET_POS 冲突；必要时标注 TODO。
- **阻塞动画**：长链/大树会卡 UI，控制 `duration_ms` / `max_frames`，关键冒烟测试可减速但保持覆盖。
- **文档版本**：忘记同步 `index.md` / front matter 会导致后续 Agent 误判状态。

## 调试与问题定位提示
- **复现最小化**：编写/调整 Dev Hook，把问题缩到 2–3 个命令；或用 JSON/DSL CLI 重放。
- **查看 Ops**：在 Model 里暂存/打印（调试时）生成的 Timeline，确认 CREATE/DELETE/SET_STATE/SET_LABEL 顺序正确。
- **边/指针问题**：优先检查内存拓扑（parent/child）与 `_op_delete_edge`/`_op_create_edge` 调用顺序是否一致。
- **消息/状态残留**：确认 Restore 步骤包含所有 visited 节点与 traversed 边，并 CLEAR_MESSAGE。
- **Layout 重叠**：检查 SceneGraph 偏移表与 LayoutStrategy 路由；必要时调大 `(dx, dy)` 或添加 TODO。
- **PySide6 测试性能**：参考 `dev_kb.md` 的动画加速/禁用策略；如卡顿，缩短 `duration_ms`。
- **CI/工具**：`uv run ruff check`（风格/错误），`uv run mypy src`（类型），`uv run pytest`（全量）；遇到 uv 缓存权限可设置 `UV_CACHE_DIR=./tmp/uv-cache`。

## 如何避免漂移
- **先读后改**：修改任何核心路径前再次确认 `project_state.md` 与 `index.md`，确保不覆盖他人最新约定。
- **小步提交**：每次只改一个主题（如“BST 删除修复”），附带对应测试和文档行。
- **显式假设**：新限制/假设写入 `project_state.md` 或 `dev_kb.md`，避免隐性知识。
- **一致的状态/颜色命名**：复用 `animation.md` 推荐状态，避免自造状态字符串。
- **注册表单一入口**：新增命令/模型只改 `command_schema.py` 与注册函数，避免散落硬编码。

## 资源与查找路径
- **协议/语义**：`docs/design/ops_spec.md`。
- **状态/动画范式**: `docs/design/animation.md`。
- **模型开发模板**：`docs/design/model.md`。
- **SceneGraph 路由/注册**：`docs/design/scene_graph.md`。
- **Layout 偏移与策略**：`docs/design/layout.md`。
- **Renderer 行为/消息锚点**：`docs/design/renderer.md`。
- **问题排查**：`docs/engineering/dev_kb.md`（测试开关、已知坑）。
