# AGENTS.md — System & Agent Guide

> 本文件面向所有“开发主体”（人类开发者 + Coding Agents，例如 Codex / Copilot / Cursor 等），
> 说明本项目的目标、约束、目录结构和协作规则。

---

## 0. 项目概览

项目名称：Data Structure Visualizer（暂定）

核心目标：

1. 提供一个**教学向的数据结构与算法可视化工具**（满足课程设计要求）。
2. 构建一个**可复用的动画引擎**：数据结构模型 → 抽象动画指令（AnimationOps）→ 可插拔渲染器。
3. 当前实现为 **Python + PySide6 桌面版 MVP**，未来计划迁移到 **TypeScript + React + Canvas/WebGL**。
4. 支持扩展模块，例如 **Git 提交图可视化**，证明引擎具备通用性。

详细需求与架构说明见：

- `docs/REQUEST.md`
- `docs/ARCHITECTURE.md`
- `docs/ANIMATION_REQUIREMENTS.md`
- `docs/ENVIRONMENT.md`

---

## 1. 环境与工具栈（简要）

完整环境说明见 `docs/ENVIRONMENT.md`，这里只给简要约定：

- 语言：Python 3.11
- 依赖管理：[`uv`](https://github.com/astral-sh/uv)
- GUI 框架：PySide6（QGraphicsView / QGraphicsScene）
- 测试框架：pytest
- 开发工具（建议）：black、ruff、mypy（可选）

约定的基础命令（在项目根目录）：

```bash
# 安装依赖 / 创建虚拟环境
uv sync

# 运行应用（暂定）
uv run python -m ds_vis.ui.main_window

# 运行测试
uv run pytest
````

任何 Agent 在修改代码前，应先阅读 `docs/ENVIRONMENT.md` 并确保在本地能够完成上述命令。

---

## 2. 顶层目录结构约定

当前目标目录结构（会随项目演进细化）：

```text
.
├─ AGENTS.md                # 本文件
├─ README.md                # 面向用户/评审的项目说明（后期完善）
├─ pyproject.toml           # 项目配置（uv 使用）
├─ docs/                    # 设计与规范文档
│   ├─ REQUEST.md
│   ├─ ENVIRONMENT.md
│   ├─ ARCHITECTURE.md
│   ├─ ANIMATION_REQUIREMENTS.md
│   └─ （未来：OPS_SPEC.md, DSL_SPEC.md 等）
├─ src/
│   └─ ds_vis/
│       ├─ __init__.py
│       ├─ core/           # 模型、场景、动画指令等“引擎核心”
│       ├─ renderers/      # 渲染器实现（PySide6、未来 Web 等）
│       ├─ ui/             # 桌面 UI 逻辑
│       ├─ dsl/            # 领域专用语言解析与执行
│       └─ persistence/    # 场景保存与加载
├─ tests/                   # 单元测试
└─ examples/                # 简单使用示例
```

---

## 3. 架构红线（必须遵守）

任何人类或 Agent 在修改代码时，必须遵守以下架构约束（详细说明见 `docs/ARCHITECTURE.md`）：

1. **Model / Renderer 解耦**

   * `src/ds_vis/core/` 中的数据结构模型和场景管理代码 **不得依赖** PySide6 或其他 UI/渲染框架。
   * `src/ds_vis/renderers/` 只能依赖 `core.ops` 暴露的动画指令类型，**不得直接依赖**具体验证结构模型实现。

2. **Command & SceneGraph 为唯一入口**

   * UI / DSL / Persistence 不应直接调用模型内部方法。
   * 所有高层操作必须经过 `SceneGraph`，以 `Command` 形式下发，再由模型产生 AnimationOps。

3. **Renderer 只消费 AnimationOps**

   * 渲染器收到的输入是 `AnimationOps` 和时间线，不能绕过 Ops 直接操作核心数据结构。

4. **禁止跨层“偷懒依赖”**

   * `ui` 不得 import `renderers.pyside6` 以外的具体渲染实现。
   * `dsl` 不得 import PySide6 或任何 UI 组件。
   * `persistence` 不得依赖 UI 或渲染器。

如需突破上述规则，必须先更新 `docs/ARCHITECTURE.md` 并在 PR 中解释原因。

---

## 4. Agent 角色与权限

### 4.1 Architecture / Design Agent

* 目标：修改或补充 `docs/*.md` 中的设计文档与规范。
* 允许修改：

  * `docs/`
  * `README.md`
  * `AGENTS.md`
* 禁止修改：

  * `src/` 下任何代码（除非明确任务要求）

### 4.2 Core Implementation Agent（核心引擎实现）

* 目标：实现或修改核心引擎（模型、动画指令、SceneGraph）。
* 修改范围：

  * `src/ds_vis/core/**`
  * `tests/**`（添加或更新与核心逻辑相关的测试）
* 必须先阅读：

  * `docs/ENVIRONMENT.md`
  * `docs/ARCHITECTURE.md`
  * `docs/ANIMATION_REQUIREMENTS.md`
  * （未来）`docs/OPS_SPEC.md`

### 4.3 Renderer Implementation Agent（渲染器实现）

* 目标：实现 PySide6 渲染器及相关 UI 逻辑。
* 修改范围：

  * `src/ds_vis/renderers/**`
  * `src/ds_vis/ui/**`
  * `tests/**`（与渲染层相关的测试）
* 必须先阅读：

  * `docs/ENVIRONMENT.md`
  * `docs/ARCHITECTURE.md`
  * `docs/ANIMATION_REQUIREMENTS.md`

### 4.4 DSL / LLM Agent（后期）

* 目标：实现 DSL 解析与自然语言到命令/DSL 的映射。
* 修改范围：

  * `src/ds_vis/dsl/**`
  * `tests/**`
* 约束：

  * 不得直接接触渲染器；
  * 输出必须是统一的 `Command` 或交由 `SceneGraph` 执行。

---

## 5. 开发工作流简要约定

建议工作流（人类 / Agent 均适用）：

1. 阅读相关文档（REQUEST / ARCHITECTURE / ANIMATION / ENVIRONMENT）。
2. 确认当前任务所属角色（Core / Renderer / DSL / Docs）。
3. 限定修改范围在该角色允许的目录内。
4. 保持 `uv sync` 可通过，`uv run pytest` 无错误。
5. 提交信息应简洁且语义清晰，例如：

   * `feat(core): add basic BST model`
   * `feat(renderer): implement node highlight animation`
   * `docs(animation): refine AVL rotation micro-steps`

---

> 本文件会随着项目演进进行更新。
> 任何开发者（包括人类 / Agent）如果修改了相关内容，应当同步更新本文件
