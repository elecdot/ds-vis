# ARCHITECTURE — 架构设计说明（v0.1）

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
````

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
3. 将 Model 返回的 AnimationOps 序列汇总，供 Renderer 播放。
4. 提供当前场景状态的导入/导出接口，供 Persistence 使用。

SceneGraph **不做**：

* 具体动画实现（由 AnimationOps + Renderer 负责）；
* UI 逻辑；
* DSL 文本解析。

---

## 4. AnimationOps 与 Renderer

### 4.1 AnimationOps

AnimationOps 是一组用于描述“动画应该如何执行”的抽象指令，例如：

* 结构性变化：

  * `CreateNode`
  * `DeleteNode`
  * `CreateEdge`
  * `DeleteEdge`
* 视觉效果：

  * `MoveNode`
  * `HighlightNode`
  * `SetLabel`
* 控制结构：

  * `Wait`
  * `Sequence`
  * `ParallelGroup`

**关键原则：**

* Model 与 SceneGraph 只需要组合这些 Ops，不关心它们在 PySide6 / Web 上如何具体实现。
* Renderer 只消费 Ops，不知道也不关心 BST/AVL 的内部逻辑。

详细的 Ops 规范会在后续 `OPS_SPEC.md` 中定义。

### 4.2 Renderer

`renderers/base.py` 中定义一个抽象 Renderer 接口，例如：

* `render(ops: Sequence[AnimationOp]) -> None`

具体实现：

* `renderers/pyside6/`：将节点映射到 QGraphicsItem，将 Ops 映射到动画。
* 未来 `renderers/web/`：将节点映射到 Canvas/WebGL 对象。

---

## 5. 依赖方向与禁止规则

为保持架构清晰，规定以下依赖方向：

* `core` 不得依赖 `renderers`、`ui`、`dsl`、`persistence`。
* `renderers` 可以依赖 `core.ops`、`core.layout`，但不得直接依赖 `core.models` 内部细节。
* `ui` 可以依赖 `renderers` 和 `core.scene`（通过 Command 与 SceneGraph 交互），不得直接依赖 `core.models`。
* `dsl` 可以依赖 `core.scene.Command`，不得依赖渲染相关代码。
    - DSL 与 Git 模块的交互方式一致：DSL 解析 Git 子域语法后仅生成 Command，不直接访问 GitGraphModel。
* `persistence` 通过 `SceneGraph` 导入/导出结构状态，不直接操纵 Model 内部。

若需要打破上述规则，必须在文档中说明原因并经过审慎评估。

---

## 6. 当前阶段的实现优先级

按优先级排序：

1. 文档与接口设计（本文件 + REQUEST + ENVIRONMENT + ANIMATION）。
2. `core.scene` 中 `Command` 与 `SceneGraph` 的接口定义（可先为空实现）。
3. `core.ops` 中 AnimationOps 类型骨架与 Timeline 接口。
4. 一个最小的 PySide6 Renderer 与空窗口 UI（用于验证环境与依赖无误）。