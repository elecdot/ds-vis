---
bound_phase: P0.3
version: rolling
status: Living
last_updated: 2025-12-14
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

- **[Limitation][Layout]** SimpleLayout is single-row with global `start_y`; no multi-structure spacing; always emits `SET_POS` for all nodes (no dirty check), inflating timelines for larger scenes.
- **[Limitation][Renderer]** PySide6 renderer hardcodes colors/shapes and ignores `duration_ms`; timing/skins need design before widening scope.
- **[Risk][IDs]** ID stability only implemented for list create/delete-recreate; other structures still index-derived and will rename on mutation.
- **[Limitation][Commands]** Command handler registry存在但命令面极小（list create/delete）；payload 校验为最小必填/类型检查，后续扩展需更严格 schema。
- **[Limitation][UI]** Main window is a dev playground; lacks play/pause/step/speed to surface timing bugs and manage multiple structures.
- **[Gap][Tests]** Coverage thin beyond walking skeleton; timing semantics, BST/GitGraph ops, and error-path checks still missing.
- **[Stub][Models]** BST/GitGraph models are skeletons emitting empty timelines; only list `CREATE_STRUCTURE` is implemented.
- **[Limitation][CommandCoverage]** Supported命令面仍极小（list create + delete index/all）；其他操作均抛 `CommandError`。
- **[Limitation][AnimationDepth]** List animations are L1（结果态）级别，仅覆盖 create/delete/recreate；缺少细化的教学步骤（L2+）。
