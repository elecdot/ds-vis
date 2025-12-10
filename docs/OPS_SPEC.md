# OPS_SPEC — AnimationOps 规范（v0.1）

本规范定义了本项目中 “动画指令层（AnimationOps）” 的统一协议，  
用于在 **模型 / SceneGraph** 与 **渲染器** 之间传递“应该展示什么动画”。

目标：

- 与数据结构模型、UI、DSL 解耦。
- 与具体渲染技术解耦（PySide6 / Web / CLI）。
- 适合序列化为 JSON（方便 DSL、Web、跨进程）。

---

## 1. 总体设计思想

### 1.1 基本单位：Step + Ops

动画被抽象为一个 **按顺序播放的 Step 列表**：

- 每个 **Step** 有一个统一的 `duration_ms`（时长）。
- 一个 Step 内部包含若干个 **AnimationOp**，它们被认为是**并行发生**的。
- 渲染器负责在 `duration_ms` 时间窗口内，从上一 Step 状态平滑过渡到当前 Step 状态。

这意味着：

- 时间轴只在 Step 这一层出现（不在单个 Op 上控制时间）。
- 绝大部分教学动画可以看作 “一系列状态切换 + 每一步的过渡效果”。

### 1.2 对象模型：Node / Edge / Global

AnimationOps 操作的对象分为三类：

- **Node**：可视化中的基本元素（数组格、链表结点、树结点、Git commit 等）。
- **Edge**：节点之间的连接（指针、树边、Git 父子关系, 可能有方向）。
- **Global**：全局提示文本等，不属于具体节点或边。

### 1.3 ID 约定

- `node_id` / `edge_id` / `structure_id` 等 ID 均为字符串。
- ID 由模型/SceneGraph 负责分配，渲染器只使用，不修改。

---

## 2. Timeline 结构

### 2.1 概念结构

一个完整动画时间线用以下结构表示：

```jsonc
{
  "steps": [
    {
      "duration_ms": 400,
      "label": "BST 插入：查找位置",
      "ops": [
        { "op": "SET_STATE", "target": "node_5", "data": { "state": "active" } }
      ]
    },
    {
      "duration_ms": 400,
      "label": "BST 插入：创建新节点",
      "ops": [
        { "op": "CREATE_NODE", "target": "node_7", "data": { "structure_id": "tree_1", "kind": "bst_node", "label": "7" } },
        { "op": "CREATE_EDGE", "target": "edge_5_7", "data": { "from": "node_5", "to": "node_7", "directed": true } }
      ]
    }
  ]
}
````

### 2.2 Step 字段

* `duration_ms: int`

  * 本 Step 的播放时长（毫秒）。
  * 推荐默认值：300–600ms。
* `label: string | null`

  * 可选，人类可读的 Step 名，方便 UI 或调试。
* `ops: AnimationOp[]`

  * 本 Step 内要执行的所有动画操作。

---

## 3. AnimationOp 结构

统一结构：

```json
{
  "op": "OP_CODE",
  "target": "object_id or null",
  "data": { /* op-specific payload */ }
}
```

### 字段说明：

* `op: string`

  * 枚举值，指明操作类型，如 `CREATE_NODE`。
* `target: string | null`

  * 主要操作对象 ID（节点、边、或其他）。
  * 若操作是全局性质（如 `SET_MESSAGE`），可以为 `null`。
* `data: object`

  * 不同 `op` 类型的参数载荷，结构在下面逐一定义。

---

## 4. 标准 Op 集合（v0.1）

以下是 v0.1 约定的最小、可扩展 AnimationOps 集合，
它们应足以覆盖：数组、链表、栈、BST、AVL、Huffman、GitGraph 的教学动画需求。

> 重要：
>
> * 结构变化（创建、删除、连边） → 结构类操作
> * 视觉效果（高亮、淡出、标签变化） → 状态类操作
> * 全局提示（解释当前步骤） → 全局类操作

### 4.1 结构类（Structural Ops）

#### 4.1.1 `CREATE_NODE`

在画布中创建一个新的 Node。

* `target`: `node_id`
* `data`:

```json
{
  "structure_id": "tree_1",
  "kind": "bst_node",     // 由渲染器/皮肤系统解释，比如 bst_node / array_cell / git_commit
  "label": "42",          // 显示在节点上的文本
  "meta": {               // 可选，模型附带信息
    "key": 42
  }
}
```

#### 4.1.2 `DELETE_NODE`

从画布中删除一个现有 Node。

* `target`: `node_id`
* `data`: `{}`（空对象）

> 渲染器可根据当前 Step 的 `duration_ms` 决定是立即消失还是淡出。

---

#### 4.1.3 `CREATE_EDGE`

在两个 Node 之间创建一条 Edge。

* `target`: `edge_id`
* `data`:

```json
{
  "structure_id": "tree_1",
  "from": "node_5",
  "to": "node_7",
  "directed": true,
  "label": ""        // 如 "left" / "next" / "parent" 等，可选
}
```

#### 4.1.4 `DELETE_EDGE`

删除现有边。

* `target`: `edge_id`
* `data`: `{}`

---

### 4.2 布局与位置（Layout / Position Ops）

布局算法通常由 `core.layout` 决定，
AnimationOps 用于通知渲染器“某个 Node 应该在新位置”。

#### 4.2.1 `SET_POS`

设置 Node 的显示位置（坐标单位由渲染器解释，通常为像素）。

* `target`: `node_id`
* `data`:

```json
{
  "x": 120.0,
  "y": 80.0
}
```

> 渲染器可在 Step 的 `duration_ms` 时间内插值从上一位置移动到新位置，从而形成平滑移动效果。

---

### 4.3 状态与样式（State / Visual Ops）

为保持样式简单但可扩展，我们采用“**逻辑状态标签**”，具体视觉样式由渲染器自行 mapping。

#### 4.3.1 `SET_STATE`

设置 Node 或 Edge 的逻辑状态。

* `target`: `node_id` 或 `edge_id`
* `data`:

```json
{
  "state": "active"   // 例如: "normal", "active", "secondary", "to_delete", "faded", "error"
}
```

推荐状态值集合（可扩展）：

* `normal`：默认状态
* `active`：当前操作焦点节点
* `secondary`：辅助高亮（如查找路径中的非当前节点）
* `to_delete`：即将被删除的节点
* `faded`：弱化显示
* `error`：错误提示（如非法操作）

#### 4.3.2 `SET_LABEL`

修改 Node 或 Edge 的文本标签。

* `target`: `node_id` 或 `edge_id`
* `data`:

```json
{
  "text": "5"
}
```

适用于：

* 更新数组单元格内容；
* 更新树结点 key；
* 更新 Git commit 的短 SHA / message 摘要。

---

### 4.4 全局提示（Global Ops）

#### 4.4.1 `SET_MESSAGE`

设置当前 Step 的全局提示文本（例如在界面下方显示）。

* `target`: `null`
* `data`:

```json
{
  "text": "当前操作：在结点 5 的右子树插入 7"
}
```

渲染器可以选择：

* 在一个固定区域显示该文本；
* 或以浮动提示方式呈现。

#### 4.4.2 `CLEAR_MESSAGE`

清除全局提示。

* `target`: `null`
* `data`: `{}`

---

## 5. Git 教学动画中的 Ops 使用约定（示例）

以虚拟 `git commit` 动画为例，推荐使用如下 Ops 组合：

### 5.1 git commit -m "msg"

假设当前 HEAD 在 `commit_a`，新 commit 是 `commit_b`，所在结构 ID 为 `repo_1`。

1. 高亮当前 HEAD：

```json
{ "op": "SET_STATE", "target": "commit_a", "data": { "state": "active" } }
```

2. 创建新节点 + 边：

```json
{
  "op": "CREATE_NODE",
  "target": "commit_b",
  "data": {
    "structure_id": "repo_1",
    "kind": "git_commit",
    "label": "b1c2d3",
    "meta": { "message": "msg" }
  }
}
```

```json
{
  "op": "CREATE_EDGE",
  "target": "edge_a_b",
  "data": {
    "structure_id": "repo_1",
    "from": "commit_a",
    "to": "commit_b",
    "directed": true
  }
}
```

3. 设置 HEAD / branch 标签的 POS / STATE（可选）
   （HEAD / branch label 可以建模为特殊 kind 的 Node,
    绑定一条边指向特定的branch / git_commit Node）

---

## 6. Python 映射（与 core/ops 对应）

在 Python 侧，AnimationOps 规范对应如下基础类型（Phase 0–1）：

```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Mapping


class OpCode(Enum):
    CREATE_NODE = auto()
    DELETE_NODE = auto()
    CREATE_EDGE = auto()
    DELETE_EDGE = auto()
    SET_POS = auto()
    SET_STATE = auto()
    SET_LABEL = auto()
    SET_MESSAGE = auto()
    CLEAR_MESSAGE = auto()


@dataclass(frozen=True)
class AnimationOp:
    op: OpCode
    target: str | None
    data: Mapping[str, Any]
```

时间线层：

```python
from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class AnimationStep:
    duration_ms: int = 400
    label: str | None = None
    ops: List[AnimationOp] = field(default_factory=list)


@dataclass
class Timeline:
    steps: List[AnimationStep] = field(default_factory=list)

    def add_step(self, step: AnimationStep) -> None:
        self.steps.append(step)

    def __iter__(self) -> Sequence[AnimationStep]:
        return iter(self.steps)

    def __len__(self) -> int:
        return len(self.steps)
```

> 注意：
>
> * **目前只保证接口定义和语义稳定**；
> * 具体实现（如何生成这些 ops、如何在 PySide6/Web 上渲染）由后续 Phase 和 Coding Agents 实现。

---

## 7. 演进计划（v0.2+）

未来可能扩展的内容（不在当前课设硬性范围内）：

* 增加 `GROUP`/`PARALLEL` 等更复杂时间结构。
* 增加更细粒度的视觉 control（如颜色通道、线型、节点形状）。
* 增加 `ATTACH_OVERLAY`、`HIDE_NODE` 等更丰富交互。

但在当前阶段，**本规范列出的 Op 集合已经足以支持 L2 教学级动画 + Git 教学模块**。
