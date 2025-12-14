---
bound_phase: P0.2
version: v0.2
status: Stable
last_updated: 2025-12-14
---

# ENVIRONMENT — 开发与运行环境说明

## 1. 运行时环境

- 语言：Python 3.11.x
- 操作系统：
  - 推荐：Windows 11
  - 尽量保持对 Linux / macOS 的兼容（不使用平台特定路径或 API）

## 2. 工具链

- 依赖与虚拟环境管理：[`uv`](https://github.com/astral-sh/uv)
- 版本控制：Git（推荐 Git 2.30+）
- GUI 框架：PySide6
- 测试框架：pytest
- 代码风格与静态检查（建议）：
  - black
  - ruff
  - mypy（可选）

## 3. 安装步骤

在项目根目录：

```bash
# 安装依赖 / 创建虚拟环境
uv sync
````

`uv` 会根据 `pyproject.toml` 安装运行时和开发依赖，并创建虚拟环境。

## 4. 常用命令

在项目根目录执行：

```bash
# 运行应用（暂定入口，后续可根据 ui 模块设计调整）
uv run python -m ds_vis.ui.main_window

# 运行测试（自动包含覆盖率报告）
uv run pytest

# 代码格式化与 Lint 修复
uv run ruff check --fix src tests

# 静态类型检查
uv run mypy src
```

以上命令的可用性依赖于 `pyproject.toml` 中对相应工具的配置。

## 5. 约定

1. 所有开发与运行均应在 uv 创建的虚拟环境中进行，避免污染系统 Python。

2. 不建议使用全局 `pip install` 修改环境。

3. 如需添加新依赖，应通过：

   ```bash
   uv add <package-name>
   ```

   并提交更新后的 `pyproject.toml` / `uv.lock`。

4. 文档中的命令默认在项目根目录执行。

## 6. 测试与 CI 策略

本项目强制采用 **TDD (测试驱动开发)** 模式。

详细的工作流、测试分层策略和最佳实践，请**务必阅读**：
- [docs/engineering/tdd_guide.md](./tdd_guide.md)

### 6.1 CI 流水线 (GitHub Actions)

每次 Push 或 PR，CI 会自动执行以下检查：
1. **Lint**: `ruff check` (代码风格与质量)
2. **Type Check**: `mypy` (静态类型安全)
3. **Test**: `pytest` (单元与集成测试)

**任何 Agent 提交的代码必须通过 CI 检查。**

### 6.2 测试分类与开发工作流

请参阅 [TDD Guide](./tdd_guide.md) 获取关于 Unit/Integration/E2E 测试的定义以及 Red-Green-Refactor 的具体执行步骤。
