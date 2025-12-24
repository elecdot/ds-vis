---
bound_phase: P0.7
version: v0.1
status: Active
last_updated: 2025-12-24
---

# Testing & CI Integration

本文件说明 DS-Vis 项目的测试策略、工具链以及持续集成 (CI) 流程。

## 1. 测试策略

我们采用 **TDD (测试驱动开发)** 模式，确保核心逻辑（Model, Layout, SceneGraph）在交付前具备 80% 以上的覆盖率。

### 1.1 测试分类
- **单元测试 (Unit Tests)**：验证单个 Model 的逻辑（如 BST 插入、List 删除）。
- **集成测试 (Integration Tests)**：验证 SceneGraph 路由、DSL 解析以及持久化流程。
- **UI 测试 (UI Tests)**：使用 `pytest-qt` 模拟用户点击，验证渲染器与控制面板的交互。
- **回归测试 (Regression Tests)**：针对已修复的 Bug 编写专项用例（如“后继节点带右子树的删除”）。

## 2. 本地测试工具链

项目依赖 [uv](https://github.com/astral-sh/uv) 管理环境，所有测试命令均需通过 `uv run` 执行。

### 2.1 运行测试 (pytest)
```bash
# 运行全量测试
uv run pytest

# 运行特定模块测试
uv run pytest tests/core/models/

# 查看覆盖率报告
uv run pytest --cov=src/ds_vis
```

### 2.2 静态检查 (Ruff & Mypy)
- **Ruff**：用于 Linting 和代码格式化。
  ```bash
  uv run ruff check src tests
  ```
- **Mypy**：用于静态类型检查。
  ```bash
  uv run mypy src
  ```

## 3. CI 集成 (GitHub Actions)

项目配置了 GitHub Actions 自动化流水线，确保每次提交和 PR 均符合质量标准。

### 3.1 工作流配置
配置文件位于 `.github/workflows/ci.yml`（如果已创建）。主要步骤包括：
1. **环境初始化**：安装 Python 3.11 和 `uv`。
2. **依赖同步**：执行 `uv sync`。
3. **Lint 检查**：运行 `ruff`。
4. **类型检查**：运行 `mypy`。
5. **自动化测试**：运行 `pytest`。
   - *注意*：UI 测试在 CI 环境下需设置 `QT_QPA_PLATFORM=offscreen`。

### 3.2 验收标准
- 所有测试用例必须通过 (Green)。
- 核心模块覆盖率不得下降。
- 无新增 Lint 错误或类型警告。

## 4. 常见问题

### Q: CI 环境下 UI 测试报错 "Could not connect to display"
**A**: 确保在 CI 脚本中设置了环境变量：
```yaml
env:
  QT_QPA_PLATFORM: offscreen
```

### Q: 如何在本地模拟 CI 环境？
**A**: 运行以下组合命令：
```bash
uv run ruff check src tests && uv run mypy src && uv run pytest
```

---
**下一站导览：** [项目当前状态](../project_state.md)
