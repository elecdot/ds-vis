---
bound_phase: P0.5
version: rolling
status: Living
last_updated: 2025-12-15
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
- **[Limitation][Renderer]** PySide6 renderer 硬编码配色/形状，忽略 `duration_ms`，无插值/淡入淡出；皮肤与 timing 需设计。
- **[Risk][IDs]** ID 稳定性仅在 list 覆盖；其他结构仍基于索引，变更会导致重命名。
- **[Limitation][Commands]** 命令 schema/操作映射仅覆盖 list 的 CREATE_STRUCTURE/DELETE_STRUCTURE/INSERT；扩展 BST/GitGraph 需补注册表与模型 op。
- **[Limitation][UI]** Main window 仅 Dev playground：无 play/pause/seek/speed，单场景。
- **[Gap][Tests]** timing 语义、BST/GitGraph ops、渲染时序仍缺覆盖。
- **[Stub][Models]** BST/GitGraph models 仍为空壳；仅 list create/delete/insert 实现。
- **[Limitation][AnimationDepth]** Renderer 仅做 Step 结果跳变；无真实动画（插值/缓入缓出），虽有 L2 微步骤但缺少时序表现。
