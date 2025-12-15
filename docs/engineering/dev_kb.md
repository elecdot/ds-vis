---
bound_phase: P0.4
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

- **[Limitation][Layout]** SimpleLayout 2.0 仍为有状态顺序引擎，不支持 seek/倒播；默认左对齐与固定尺寸假设，未支持树/DAG 居中或可变尺寸。
- **[Limitation][Renderer]** PySide6 renderer hardcodes colors/shapes and ignores `duration_ms`; timing/skins need design before widening scope.
- **[Risk][IDs]** ID stability only implemented for list create/delete-recreate; other structures still index-derived and will rename on mutation.
- **[Limitation][Commands]** 命令 schema/操作映射仅覆盖 list 的 CREATE_STRUCTURE/DELETE_STRUCTURE/DELETE_NODE；扩展 INSERT/BST/GitGraph 需补注册表与模型 op。
- **[Limitation][UI]** Main window is a dev playground; lacks play/pause/step/speed to surface timing bugs and manage multiple structures.
- **[Gap][Tests]** Coverage thin beyond walking skeleton; timing semantics, BST/GitGraph ops, and error-path checks still missing.
- **[Stub][Models]** BST/GitGraph models are skeletons emitting empty timelines; only list `CREATE_STRUCTURE` is implemented.
- **[Limitation][AnimationDepth]** List animations are L1（结果态）级别，仅覆盖 create/delete/recreate；缺少细化的教学步骤（L2+）。
