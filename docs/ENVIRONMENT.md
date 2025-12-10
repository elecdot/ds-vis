# ENVIRONMENT — 开发与运行环境说明（v0.1）

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

# 运行测试
uv run pytest

# 代码格式化（如果已在 pyproject.toml 中配置 black）
uv run black src tests

# 静态检查（如果已配置 ruff）
uv run ruff check src tests
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