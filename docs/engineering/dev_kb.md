---
bound_phase: P0.7
version: rolling
status: Living
last_updated: 2025-12-24
---

# Developer Knowledge Base (FAQ & Troubleshooting)

> **Purpose**: This document serves as a shared "long-term memory" for Developers and Agents.
> **Rule**: If you solve a tricky environment issue, clarify a confusing architectural point, or identify a persistent limitation, **record it here**.

---

## 1. Troubleshooting (Environment & Tools)

### Q: `uv run mypy` fails with "Module not found" or import errors
**A:**
1. Ensure you are running commands from the project root.
2. Run `uv sync` to ensure the virtual environment is up to date.
3. Check if `src` is correctly recognized. `pyproject.toml` should have `pythonpath = ["src"]` in the pytest config, but mypy relies on its own config. We have `[tool.mypy]` configured to be strict.

### Q: Tests fail with `ModuleNotFoundError: No module named 'ds_vis'`
**A:**
Always use `uv run pytest`. This ensures the `src` directory is in the `PYTHONPATH`. Do not run `pytest` directly unless you have manually activated the venv.

### Q: `uv run ...` 报错无权限访问全局缓存
**A:** 在本仓库使用本地缓存目录，示例：
```
UV_CACHE_DIR=./tmp/uv-cache uv run pytest
```

### Q: UI 测试里手动推进 step 会导致结果不稳定？
**A:** 使用 `MainWindow._advance_step(schedule_next=False)` 来推进步骤，避免在渲染同步动画 (`qWait`) 时重新启动定时器导致步进错位。

---

## 2. Architecture FAQ

### Q: Why can't the Model return `SET_POS` ops?
**A:**
To enforce **Separation of Concerns**.
- **Models** (BST, List) handle *Logical Topology* (who is connected to whom).
- **Layouts** handle *Visual Geometry* (where they are on screen).
- **Renderers** handle *Drawing* (pixels/vectors).
If a Model decides positions, we cannot easily swap layouts (e.g., switching from Tree Layout to Radial Layout) or reuse the Model for a CLI output.

### Q: How do I add a new Animation Operation?
**A:**
1. Add the enum member to `OpCode` in `src/ds_vis/core/ops/ops.py`.
2. Update `docs/design/ops_spec.md` to define its payload structure.
3. Update `docs/index.md` version for OPS_SPEC.
4. Implement handling in the Renderer.

---

## 3. Known Issues & Technical Debt (Active)

> Agents: Before attempting to "fix" a bug, check if it's a known limitation.

- **[Limitation][Layout]** SimpleLayout 仍为有状态顺序引擎，不支持 seek/倒播；默认左对齐与固定尺寸假设，未支持树/DAG 居中或可变尺寸。
- **[Limitation][Renderer]** PySide6 renderer 硬编码配色/形状；动画为同步插值（qWait），无 seek/skip/异步调度，缓动固定。
- **[Risk][IDs]** ID 稳定性仅在 list 覆盖；其他结构仍基于索引，变更会导致重命名。
- **[Limitation][Commands]** 目前仅覆盖 list 的 CREATE_STRUCTURE/DELETE_STRUCTURE/DELETE_NODE/INSERT/SEARCH/UPDATE；扩展 BST/GitGraph 需补注册表与模型 op。
- **[Limitation][UI]** Main window 仅 Dev playground：单场景，无 seek/skip/多时间线管理。
- **[Gap][Tests]** timing 语义、BST/GitGraph ops、渲染时序仍缺覆盖。
- **[Stub][Models]** BST/GitGraph models 仍为空壳；仅 list create/delete/insert 实现。
- **[Limitation][AnimationDepth]** 仍缺可配置缓动/非阻塞播放；播放控制为基础版。
- **[Note][ListModel]** `create([])` 会生成 sentinel 仅用于可视化空表（display-only），当前假设空表用于展示而非逻辑操作。
- **[Note][ListModel]** `insert` 现包含遍历高亮（secondary）、旧边标记为 to_delete、新边/关键节点用 highlight，并使用 step label 便于 UI/测试定位；insert/update/search 会在步骤前后用 SET_MESSAGE，操作结束 CLEAR_MESSAGE。
- **[Gap][Animation]** 边动画（逐渐绘制/虚线删除）未实现；节点“侧边悬停”标记为 Layout 低优先需求。
- **[Risk][Ops]** `CREATE_NODE.data.kind` 目前未强制必填，Renderer/Layout 需默认回退样式；可考虑加入告警或文档强化为“强烈建议必填”。
- **[Design][Metrics]** 不同结构节点形态与度量差异明显（seqlist/stack/tree）；建议引入可选 `StyleRegistry`/`Metrics`（`kind -> shape/size`），有默认值，避免新 Model 必须管理布局/渲染。
- **[Design][Layout]** SimpleLayout 的固定 spacing 假设可能与渲染尺寸不匹配；应将尺寸/间距由配置驱动，布局不读取 renderer。
- **[Idea][Containers]** 可在 Renderer 层按 `structure_id` 绘制容器框（半透明背景+圆角边框），无需新增 Ops；用于多结构同屏可视分区。可选替代方案：多窗口展示以规避布局冲突。
