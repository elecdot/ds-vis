---
bound_phase: P0.2
version: v0.1
status: Stable
last_updated: 2025-12-14
---

# REQUIREMENTS — 项目需求与目标说明

## 1. 课程设计题目摘要

课程题目：**线性与树形数据结构的可视化模拟器**

要求要点：

- 通过图形界面（非控制台）动态展示以下结构与算法的构建与操作过程：
  1. 线性结构
     - 顺序表、链表：构建、插入、删除
     - 栈：构建、入栈、出栈
  2. 树结构
     - 二叉树：链式存储结构构建
     - 二叉搜索树（BST）：构建、查找、删除
     - 哈夫曼树：构建过程
  3. 布局良好、信息完整的可视化展示

扩展要求（选做）包括但不限于：

- 保存与加载已绘制的数据结构，并支持再次编辑
- AVL 树构建与平衡旋转调整过程的展示
- 使用自定义 DSL 描述数据结构并自动绘制
- 利用 LLM 接收自然语言描述并生成相应数据结构与操作

课程要求还强调：

- 业务逻辑（数据结构与算法）应与 UI 分离，建议采用 MV/MVC 等模式。
- DSL 解析可使用 Lexer/Parser 框架，如 ANTLR 等。

---

## 2. 本项目在课程要求上的扩展

在满足课程要求的基础上，本项目额外目标：

1. 构建一个**可扩展的数据结构可视化引擎**，而非一次性 Demo 程序。
2. 明确分层：
   - 数据结构模型（Model）
   - 场景管理与统一命令（SceneGraph + Command）
   - 抽象动画指令（AnimationOps + Timeline）
   - 渲染器（PySide6 / 未来 Web）
   - UI / DSL / Persistence
3. 支持**教学级动画**：对操作过程进行微步骤拆分（micro-steps），便于讲解与理解。
4. 预留 DSL 和 LLM 集成能力：
   - DSL 将高层操作描述为命令，交由 SceneGraph 和 Model 执行。
   - LLM 将自然语言转换为 DSL 或 Command 序列。
5. 增加一个 **Git 提交图可视化与教学模块**：
   本模块不实现真实 Git 客户端，而是构建一个简化的 Git 内部数据结构模型（GitGraph）。
   动画仅演示 Git 内部的结构变化，包括：
   - commit DAG（父子关系）
   - HEAD、branch ref 的移动
   - merge 产生的双父节点
   为使该模块具备教学价值，将支持一组“虚拟 Git 操作”命令（不与本地仓库交互）：
   - git init
   - git commit -m "<msg>"
   - git branch <name>
   - git checkout <name>
   - git merge <name>（简化版，无冲突）
   所有虚拟 Git 命令将通过 DSL 或 UI 转换为内部 Command，由 SceneGraph 和 GitGraphModel 
   执行并返回 AnimationOps。
   该功能旨在展示 **Git 内部数据结构与指针移动的教学动画**以及本项目良好的扩展性，而非实现文件系统层面的 Git 行为。


---


## 3. 功能范围（v0.1 和 v0.2）

### 3.1 v0.1 必做功能

- 顺序表、链表、栈：构建 + 操作动画
- BST：构建 + 查找、删除
- Huffman Tree：构建动画
- 基本 SceneGraph（单场景 + 单数据结构）
- 基本 PySide6 Renderer（QGraphicsView 框架 + 节点/边渲染）
- 基础 Persistence（保存当前数据结构状态）
- Git DAG：**commit 新节点 + HEAD 切换** 的基本动画

### 3.2 v0.2 扩展

- AVL 树：平衡检测 + 旋转动画
- DSL：文本语法 → Command 序列
- Git 教学操作动画（虚拟 Git 子集）：
  - git init / commit / branch / checkout / merge 的结构变化动画
  - 支持通过 DSL 脚本执行 Git 教学序列
  - 支持特殊的Persistence（例如导入`.git` repo）
- SceneGraph：多数据结构同场景
- Persistence：保存动画历史 / 回放

## 4. 非目标（当前阶段不做）

以下内容暂不在当前课设范围内：

- 完整的 Git 客户端功能（commit、rebase、merge 等实际 Git 操作）。
- 分布式场景同步、多用户协作。
- 针对超大型数据集（> 数千节点）的性能优化。
- 所有数据结构的严肃性能 benchmark。

这些内容可在课程结束后作为长期优化方向考虑。