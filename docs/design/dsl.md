---
bound_phase: P0.7
version: v0.2
status: Active
last_updated: 2025-12-24
---

# DSL 设计说明

本文件描述当前阶段的 DSL 语法设计、解析逻辑与交互支持。

## 1. 目标与范围
- 目标：提供从文本输入到 `Command` 序列的闭环，支持自然指令操控数据结构。
- 范围：`parse_dsl`（支持文本语法与 JSON）、`run_commands`、UI 交互式注入、注释与多行支持。
- 特色：支持 Late-binding 类型推断，允许 DSL 操作 UI 创建的结构。

## 2. 语法规范 (v0.2)
### 2.1 基础格式
- 语句以 `;` 或**换行符**分隔。
- 支持 `#` 开头的单行注释。
- 字符串使用双引号 `"`。

### 2.2 结构创建 (Assignment)
格式：`<kind> <id> [= [values...]]`
- 示例：`list L1 = [1, 2, 3]`
- 示例：`bst B1` (创建空树)
- 支持跨行列表：
  ```python
  list L1 = [
    1,
    2
  ]
  ```

### 2.3 结构操作 (Command)
格式：`<op> <id> [args...]`
- 插入：`insert <id> <index?> <value?>` (如 `insert L1 1 99`)
- 删除：`delete <id> <index?>` 或 `delete <id> val=<value>`
- 搜索：`search <id> <value>`
- 栈操作：`push <id> <value>` / `pop <id>`
- Git 操作：`git <id> init` / `commit <id> "msg"` / `checkout <id> main`

## 3. 核心特性
### 3.1 上下文感知与 Late-binding
- **解析时推断**：`parse_dsl` 接受 `existing_kinds` 参数。如果在同一脚本中先创建了 `list L1`，后续的 `insert L1` 会自动识别 `L1` 为 `list` 类型。
- **运行时推断**：如果 DSL 中未指定类型且解析器无法推断（例如操作 UI 预先创建的结构），`SceneGraph` 会在执行时根据 `structure_id` 自动补全 `kind`。

### 3.2 鲁棒的词法分析
- 自动处理 `L1=[1,2]`（无空格赋值）等紧凑写法。
- 保持 `[...]` 内部的完整性，不受空格影响。

## 4. 交互入口
- **Interactive DSL (UI)**：控制面板新增按钮，支持在当前场景注入指令。
- **Dev Hook**：MainWindow 菜单支持批量执行 DSL 脚本。
- **CLI**：支持通过命令行执行 DSL 文件。

## 5. 关联文件
- `src/ds_vis/dsl/parser.py`：核心解析器。
- `src/ds_vis/core/scene/scene_graph.py`：处理 Late-binding 逻辑。
- `src/ds_vis/ui/main_window.py`：UI 交互实现。
