---
bound_phase: P0.2
version: v0.2
status: Stable
last_updated: 2025-12-14
---

# ARCHITECTURE — 架构设计说明

## 1. 顶层分层结构

本项目采用分层架构，将“算法逻辑 / 场景状态 / 动画指令 / 渲染器 / UI”明确拆分：

```text
UI / DSL / LLM
        │
        │ (Command)
        ▼
 SceneGraph  ——  Persistence
        │
        │ (调用 Model，更新内部状态)
        ▼
     Models (数据结构：List / Stack / BST / AVL / Huffman / GitGraph ...)
        │
     Layout 模块注入：SET_POS Ops
        │ (AnimationOps + Timeline)
        ▼
 Animation Engine
   (AnimationOps 类型 + 时间线管理)
        │
        │
        ▼
 Renderers
   ├─ PySide6 Renderer （当前 MVP）
   └─ 未来：Web Renderer (React + Canvas/WebGL)
```

**错误处理 (Error Handling)** 贯穿全层：
- Model 抛出逻辑异常
- SceneGraph 抛出场景异常
- UI/DSL 统一捕获并展示

目标：

* Renderer 完全独立于数据结构实现；
* DSL / LLM / UI 通过统一命令接口与 SceneGraph 交互；
* Persistence 只需与 SceneGraph 打交道，即可恢复/保存当前场景。

---

## 2. 模块划分与目录

对应 `src/ds_vis/` 下的模块规划如下：

```text
src/ds_vis/
  core/
    models/       # 各种数据结构模型：list, stack, bst, avl, huffman, gitgraph
                  # - gitgraph 用于表示简化的 Git 提交图（commit DAG）、分支引用与 HEAD 状态。
    ops/          # AnimationOps 类型定义与时间线（timeline）管理
    scene/        # Command 类型与 SceneGraph（统一场景状态）
    layout/       # 布局算法（树布局、线性布局、Git DAG 布局）
    exceptions.py # 统一异常定义
  renderers/
    base.py       # 抽象 Renderer 接口
    pyside6/      # PySide6 渲染器具体实现
  ui/
    main_window.py  # PySide6 主窗口与交互控件
    # 其他 UI 组件 ...
  dsl/
    # DSL 解析与执行（后期实现）
  persistence/
    # 场景保存与加载
```

---

## 3. SceneGraph 与 Command

### 3.1 Command

`Command` 表达的是“对某个数据结构进行某种高层次操作”，而不是低层动画指令。

示例：

* 对 BST 插入一个值：`INSERT` with payload `{ "value": 5, "structure_type": "bst" }`
* 创建一个链表：`CREATE_STRUCTURE` with payload `{ "kind": "list", "values": [1,2,3] }`

Command 是：

* UI 按钮点击的统一抽象；
* DSL 解析的统一输出形式；
* Persistence 回放操作历史的基础单位。

### 3.2 SceneGraph

`SceneGraph` 负责：

1. 管理所有当前存在的结构实例（list / stack / bst / avl / gitgraph 等）。
2. 接受 `Command`，路由到正确的 Model 实例与方法。
3. 接收 Model 返回的 Timeline 调用 Layout 完成 Timeline，供 Renderer 播放。
4. 提供当前场景状态的导入/导出接口，供 Persistence 使用。

SceneGraph **不做**：

* 具体动画实现（由 AnimationOps + Renderer 负责）；
* 数据结构模型逻辑（由 Model 负责）；
* 布局计算（由 Layout 负责）；
* UI 逻辑（由 UI 负责）；
* DSL 文本解析（由 DSL 负责）。

---

## 4. 错误处理 (Error Handling)

为了保证系统的健壮性，我们定义了统一的异常层级：

### 4.1 异常类定义 (`src/ds_vis/core/exceptions.py`)

*   `DsVisError`: 所有自定义异常的基类。
*   `SceneError`: 场景操作失败（如找不到 ID）。
*   `ModelError`: 逻辑非法（如空栈弹出）。
*   `LayoutError`: 布局计算失败。
*   `CommandError`: 指令参数错误。

### 4.2 处理策略

1.  **Model 层**: 遇到非法操作（如 `pop` 空栈）应抛出 `ModelError`，而不是返回空 Timeline 或崩溃。
2.  **SceneGraph 层**: 负责捕获 `ModelError` 或验证 `Command`，必要时抛出 `SceneError`。
3.  **UI / DSL 层**: 是异常的**最终捕获者**。
    *   UI 应捕获 `DsVisError` 并通过弹窗或状态栏提示用户（不要 Crash）。
    *   DSL 应捕获异常并输出错误行号和原因。

---

## 5. Model 层

### 5.1 核心职责

Model 层维护**真实的数据结构内部状态**，并在每次操作后生成相应的"结构 Ops"。它的核心职责是：

1. **维护数据结构状态**：
   - 管理真实的树、链表、栈等的内部状态（指针、值、平衡因子等）
   - 状态驱动完全由数据结构本身的逻辑决定

2. **生成结构 Ops**：
   - 将每次操作拆解为一系列 AnimationOps
   - 只关注**结构变化**（CREATE_NODE、DELETE_NODE、CREATE_EDGE、SET_STATE、SET_LABEL 等）
   - **不得包含任何布局信息**（如坐标、位置）

### 5.2 Model 层的约束

Model 层**禁止**：

- 依赖 Renderer、UI、DSL 或其他高层模块
- 使用 PySide6 或任何 UI 框架 API
- 依赖或生成 Timeline（Timeline 是上层的职责）
- 处理或使用坐标、位置等**视觉属性**（这是 Layout 的职责）
- 修改 SceneGraph 的内部状态
- 进行任何 UI 逻辑判断

**关键设计思想**：Model 层应该就像一个"不知道自己会被可视化"的纯数据结构库，完全独立可用。

---

## 6. Layout 层

### 6.1 核心职责

Layout 引擎是 Model 和 Renderer 之间的"几何中介"。它负责：

1. **理解结构信息**：
   - 接收 Model 层生成的结构 Ops
   - 理解数据结构的拓扑信息（树深、链表长度、节点关系等）

2. **计算几何布局**：
   - 基于数据结构的拓扑，计算每个 Node 应该在哪里（x, y 坐标）
   - 支持多种布局算法（树布局、线性布局、DAG 布局等）
   - 考虑教学效果（如保持节点间距、避免重叠等）

3. **注入 SET_POS Ops**：
   - 在 Model 生成的 Ops 中的**关键步骤**插入 SET_POS Ops
   - 保证坐标的生成时机与结构变化同步
   - 返回完整的"可渲染 Ops 序列"（结构 Ops + SET_POS Ops）

### 6.2 Layout 层的约束

Layout 层**禁止**：

- 修改或删除结构类 Ops（如不应改写 CREATE_NODE 的内容）
- 推测数据结构的语义或业务逻辑（只应理解其拓扑结构）
- 与 Model 层形成双向依赖（单向流向：Model → Layout）
- 与 Renderer 层的双向耦合（只输出 Ops，不关心如何渲染）

**关键设计思想**：Layout 是一个**纯几何计算层**，在不理解具体数据结构业务的情况下，也能为任何结构类型计算合理的坐标。
**Layout 的信息来源**：Ops 流 + 拓扑查询接口


---

## 7. AnimationOps 与 Renderer

### 7.1 AnimationOps 层次与 Timeline

AnimationOps 被组织为按顺序播放的 **Timeline**，由若干 **AnimationStep** 组成：

* **AnimationStep**：一个教学上的原子步骤，包含：
  - `duration_ms`：该步骤的播放时长（毫秒）
  - `label`：可选的人类可读标签
  - `ops`：属于本步骤的所有 AnimationOp（并行执行）

* **AnimationOp**：原子级动画指令，描述单个状态变化：

  * `CREATE_NODE`、`DELETE_NODE`、`CREATE_EDGE`、`DELETE_EDGE`（结构变化）
  * `SET_POS`（布局与位置）
  * `SET_STATE`、`SET_LABEL`（状态与样式）
  * `SET_MESSAGE`（全局提示）

**关键设计原则：**

* Op 本身不带时间概念，只描述终态；时间控制统一在 Step 层面。
* 一个 Step 内的所有 Ops 应语义上属于同一个教学微步骤，Renderer 可顺序处理它们。
* Model 与 SceneGraph 只需要组合这些 Ops，不关心它们在 PySide6 / Web 上如何具体实现。
* Renderer 只消费 Ops 与 Timeline，不知道也不关心 Model 的内部逻辑。

**详细规范**见 [`ops_spec.md`](./ops_spec.md)，该文档定义了：

- Timeline 与 Step 的完整 JSON 结构
- 标准 Op 集合（v0.1）：`CREATE_NODE`、`DELETE_NODE`、`CREATE_EDGE`、`DELETE_EDGE`、`SET_POS`、`SET_STATE`、`SET_LABEL` 等
- Op 的参数格式与语义
- 对象 ID 约定与样式映射

### 7.2 Renderer 接口与职责

**核心接口**：

Renderer 接收一个 **Timeline**（由若干 AnimationStep 组成），并负责将其播放为可视化动画。例如:

* `render(self, timeline: Timeline) -> None:`

**核心职责**：

1. **维护可视状态**：
   - 当前所有可见的 Node、Edge 及其属性（位置、样式、标签等）
   - 全局消息或提示

2. **步进式播放**：
   - 对于每个 Step，从前一状态作为起点
   - 应用本 Step 的所有 Ops，计算终态
   - 在 `duration_ms` 内，从起点插值到终态（支持平滑过渡）
   - Step 结束时的状态成为下一 Step 的起点

3. **Ops 解释**：
   - 根据 Op 类型（CREATE_NODE / SET_POS / SET_STATE 等）更新可视状态
   - 具体渲染细节（颜色、形状、字体等）由 Renderer 自行决定

4. **不关心**：
   - 数据结构模型的内部逻辑
   - 如何生成这些 Ops（那是 Model 和 SceneGraph 的职责）

**具体实现**：

* `renderers/pyside6/`：
  - 使用 QGraphicsScene/QGraphicsView
  - 将 Node 映射到 QGraphicsItem
  - 使用 QPropertyAnimation 实现过渡动画
  
* 未来 `renderers/web/`：
  - 使用 Canvas/WebGL
  - 实现相同的 Timeline 播放协议

---

## 8. 依赖方向与架构约束

### 8.1 依赖方向（Data Flow）

代码的依赖应该严格遵循从上到下的单向流向：

```
UI / DSL / Persistence
        ↓
    SceneGraph
        ↓
     Models (生成结构 Ops)
        ↓
     Layout (注入坐标 Ops)
        ↓
    Renderer (消费 Ops)
```

**反向依赖（向上依赖）是绝对禁止的。**

### 8.2 具体约束规则

| 层级 | 允许依赖 | 禁止依赖 |
|------|---------|----------|
| **Models** | 无（仅内部）| Renderer, UI, DSL, Layout, SceneGraph |
| **Layout** | core.models（结构理解）, core.ops | Renderer, UI, DSL, SceneGraph |
| **Renderer** | core.ops | Models（内部实现）, UI, DSL, SceneGraph |
| **SceneGraph** | core.models, core.layout, core.ops | Renderer, UI, DSL（反向） |
| **UI** | core.scene（通过 Command）, renderers | core.models 内部细节 |
| **DSL** | core.scene.Command | Models, Renderer, UI（内部细节） |
| **Persistence** | core.scene（导出/导入）| Models 内部 |

### 8.3 违规处理

若需要打破上述规则（如循环依赖、跨层耦合），必须：

1. 在 PR 中明确说明原因
2. 更新本文档解释例外情况  
3. 通过代码审查
4. 考虑是否需要重构来消除耦合

---

## 9. 当前阶段的实现优先级

按优先级排序：

1. 文档与接口设计（本文件 + requirements + environment + animation）。
2. `core.scene` 中 `Command` 与 `SceneGraph` 的接口定义（可先为空实现）。
3. `core.ops` 中 AnimationOps 类型骨架与 Timeline 接口。
4. 一个最小的 PySide6 Renderer 与空窗口 UI（用于验证环境与依赖无误）。