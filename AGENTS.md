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

- `docs/INDEX.md` (文档版本注册表 - **Agent 必读**)
- `docs/REQUEST.md`
- `docs/ARCHITECTURE.md`
- `docs/ANIMATION_REQUIREMENTS.md`
- `docs/ENVIRONMENT.md`
- `docs/OPS_SPEC.md`
- `docs/DEV_KNOWLEDGE_BASE.md` (FAQ / Troubleshooting / Known Issues)
- `.github/pull_request_template.md` (项目验收最小标准)

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
uv run ruff check src tests # Linting
uv run my py src            # Type check
uv run pytest               # All tests
```

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
│   ├─ INDEX.md             # Doc-Code Binding 文档
│   ├─ REQUEST.md
│   ├─ ENVIRONMENT.md
│   ├─ ARCHITECTURE.md
│   ├─ ANIMATION_REQUIREMENTS.md
│   ├─ OPS_SPEC.md
│   └─ (未来的DSL_SPEC.md 等)
├─ src/
│   └─ ds_vis/
│       ├─ __init__.py
│       ├─ core/           # 引擎核心（模型、布局、动画指令、场景图）
│       │   ├─ models/     # 数据结构模型（BST、GitGraph 等）
│       │   ├─ layout/     # 布局算法与几何计算
│       │   ├─ ops/        # 动画指令协议（AnimationOps、Timeline）
│       │   ├─ scene/      # 场景图与命令分发（SceneGraph、Command）
│       ├─ examples/       # 供参考的示例展示   
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

### 3.1 三层核心分离（Model / Layout / Renderer）

**Model 层**不得依赖：
- Renderer、UI、DSL、Layout、SceneGraph
- 任何 UI 框架（PySide6、Tkinter 等）
- 坐标、位置等视觉属性

**Layout 层**不得依赖：
- Renderer、UI、DSL、SceneGraph
- 修改结构类 Ops（CREATE_NODE、DELETE_NODE 等）
- 推测或依赖数据结构的业务逻辑

**Renderer 层**不得依赖：
- Model 内部实现细节
- UI、DSL、SceneGraph
- 直接操纵核心数据结构（只能通过 Ops）

### 3.2 单向依赖流向

所有依赖必须遵循自上而下的单向流向：

```
UI / DSL / Persistence
        ↓
    SceneGraph
        ↓
     Models (生成结构 Ops)
        ↓
     Layout (注入 SET_POS Ops)
        ↓
    Renderer (消费 Ops)
```

**反向依赖是绝对禁止的**（如 Renderer 不得调用 Model 的方法）。

### 3.3 Command & SceneGraph 为唯一高层入口

- UI / DSL / Persistence **不应直接调用**模型内部方法
- 所有高层操作必须经过 `SceneGraph`，以 `Command` 形式下发
- SceneGraph 负责路由：Models（生成 Ops）→ Layout（注入坐标）→ Renderer（播放）

### 3.4 Ops 作为唯一的跨层通信协议

- Models 只生成**结构 Ops**（CREATE_NODE、SET_STATE、SET_LABEL 等）
- Layout 注入**位置 Ops**（SET_POS）
- Renderer 消费完整的 **Ops 序列**，不得绕过 Ops 层直接修改状态
- Ops 定义见 `docs/OPS_SPEC.md`

### 3.5 禁止跨层"偷懒依赖"

- `ui` 不得直接 import `core.models` 内部（只通过 SceneGraph）
- `dsl` 不得 import PySide6 或任何 UI 组件
- `persistence` 不得直接修改 Model 内部状态
- 任何"为了快速开发"而违反此规则的代码，必须在 PR 中明确说明并通过审查

### 3.6 错误处理规范

- **Model 层禁止吞掉异常**：遇到逻辑错误（如空栈弹出）必须抛出 `ds_vis.core.exceptions` 中定义的异常。
- **Model 层禁止直接 UI 交互**：严禁使用 `print()` 或 `QMessageBox` 报错。
- **UI 层负责兜底**：UI 必须捕获 `DsVisError` 并友好展示，防止程序崩溃。

若需突破上述规则，必须：

1. 先更新 `docs/ARCHITECTURE.md` 解释例外情况
2. 在 PR 中详细说明原因和替代方案研究
3. 经过代码审查同意
4. 考虑未来的重构计划消除这个耦合

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

* 目标：实现或修改核心引擎中的**模型层和场景图**（不包括布局引擎）。
* 修改范围：

  * `src/ds_vis/core/models/**`（数据结构模型）
  * `src/ds_vis/core/ops/**`（动画指令定义）
  * `src/ds_vis/core/scene/**`（SceneGraph 与 Command）
  * `tests/**`（添加或更新与模型逻辑相关的测试）
* 必须先阅读：

  * `docs/ENVIRONMENT.md`
  * `docs/ARCHITECTURE.md`（第 4 部分：Model 层责任）
  * `docs/ANIMATION_REQUIREMENTS.md`
  * `docs/OPS_SPEC.md`（Ops 协议定义）

### 4.3 Layout Implementation Agent（布局引擎实现）

* 目标：实现布局算法和几何计算引擎。
* 修改范围：

  * `src/ds_vis/core/layout/**`
  * `tests/**`（与布局相关的测试）
* 必须先阅读：

  * `docs/ENVIRONMENT.md`
  * `docs/ARCHITECTURE.md`（第 5 部分：Layout 层责任）
  * `docs/OPS_SPEC.md`（SET_POS Ops 规范）
* 约束：

  * 不得依赖 Model 的具体实现；
  * 不得修改结构 Ops（CREATE_NODE、DELETE_NODE 等）；
  * 只能注入 SET_POS Ops；
  * 不得推测数据结构的业务逻辑，仅基于以下两种方式获取信息：
    1. **从 AnimationOps 序列推断拓扑结构**
    2. **查询 Model 的公开拓扑接口**

---

### 4.4 Renderer Implementation Agent（渲染器实现）

* 目标：实现 PySide6 渲染器及相关 UI 逻辑。
* 修改范围：

  * `src/ds_vis/renderers/**`
  * `src/ds_vis/ui/**`
  * `tests/**`（与渲染层相关的测试）
* 必须先阅读：

  * `docs/ENVIRONMENT.md`
  * `docs/ARCHITECTURE.md`
  * `docs/ANIMATION_REQUIREMENTS.md`

### 4.5 DSL / LLM Agent（后期）

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
2. 确认当前任务所属角色（Core / Layout / Renderer / DSL / Docs）。
   - 确认修改范围
   - 读取所需的全部上下文信息, 并检查信息是否过时.
   - 读取并确认活跃文档`DEV_KNOWLEDGE_BASH.md`中相关的开发信息.
3. 限定修改范围在该角色允许的目录内。
4. **检查测试状态**：
   - 运行 `uv run pytest`。
   - 如果有 `xfail` (Expected Fail) 的测试，优先实现逻辑使其通过。
   - 如果没有相关测试，先编写一个“红灯”测试（Red Test）来定义预期行为。
5. 编写代码，直到测试通过（Green）。
   - 详细流程见`.github/pull_request_templates.md`
6. 提交信息应简洁且语义清晰，例如：

   * `feat(core): add basic BST model`
   * `feat(renderer): implement node highlight animation`
   * `docs(animation): refine AVL rotation micro-steps`


## 6. 文档版本控制 (Doc-Code Binding)

本项目实行严格的“文档-代码绑定”策略，以防止设计与实现脱节。

**规则：**
1. **Registry Check**: 在修改任何代码前，检查 `docs/INDEX.md` 中的 "Bound Code Paths"。
2. **Co-evolution**: 如果你修改了某个模块（例如 `src/ds_vis/core/ops`），你必须检查并更新对应的文档（`docs/OPS_SPEC.md`）。
3. **Version Bump**: 如果文档内容发生了实质性变更（如接口修改），请在 `docs/INDEX.md` 中更新该文档的版本号和日期。

---

> 本文件以及相关文档会随着项目演进进行更新。
> 任何开发者（包括人类 / Agent）如果修改了相关内容，应当同步更新本文件及相关文档
