---
bound_phase: P0.7
version: v0.1
status: Draft
last_updated: 2025-12-24
---

# DSL 设计说明（占位版）

本文件描述当前阶段的 DSL 入口形态、假设与未来期望。现阶段 DSL 仅为“JSON 兼容占位”，便于快速贯通 SceneGraph/命令验证链路，不代表最终语法设计。

## 1. 目标与范围
- 目标：提供从文本输入到 `Command` 序列的最小闭环，便于 CLI/UI/LLM 入口测试。
- 范围：`parse_dsl`（接受 DSL/JSON）、`run_commands`（执行到 SceneGraph）、最小 CLI/UI 钩子。
- 不在范围：真实 DSL 语法、语义检查、高亮/补全、命名空间与变量、交互式调试。

## 2. 当前行为（v0.1 占位）
- 语法：接受 JSON 数组，每个元素需包含 `structure_id`、`type`（CommandType 名字）、`payload`（含 `kind` 等）。
- 校验：解析后委托 `persistence/json_io` 通过 `SCHEMA_REGISTRY` 校验 payload，抛 `CommandError`。
- 接口：
  - `parse_dsl(text: str) -> List[Command]`：JSON 直通。
  - `run_commands(commands, scene_graph)`：逐条调用 `SceneGraph.apply_command`。
  - `dsl.cli.run_cli`：支持 `--text/--file/stdin`，执行后打印执行条数，错误写 stderr。
  - UI Dev Hook：MainWindow “Run DSL/JSON” 菜单，弹出多行输入框，执行后立即播放 Timeline。

## 3. 假设与限制
- 输入默认可信为 JSON 占位；未做真实 DSL 语法/语义解析。
- 无状态管理：执行即生效，不支持撤销/重放/断点。
- 渲染仍为同步阻塞播放；大批量命令可能造成 UI 卡顿。
- 错误提示：CLI 仅打印；UI 通过 `QMessageBox`，无定位/高亮。
- 没有变量/宏/作用域设计，结构 ID 需显式提供。

## 4. 未来期望（待定方向）
- 真实 DSL：类 SQL/指令式语法（如 `use list1; insert index:1 value:10`），编译为 Command 序列。
- 语义检查：静态校验结构存在性、索引范围预判，错误可定位到行列。
- 交互体验：语法高亮、补全、错误高亮；支持“dry-run”预览命令序列。
- 执行模型：可配置动画速度/禁用；支持批处理/分步执行/撤销。
- 安全性：输入沙箱化，避免任意代码执行；LLM 生成命令的二次验证。

## 5. 关联文件
- `src/ds_vis/dsl/parser.py`：核心解析/执行 helper。
- `src/ds_vis/dsl/cli.py`：CLI 入口。
- `src/ds_vis/ui/main_window.py`：Dev 菜单 DSL/JSON 输入钩子。
- `docs/design/json.md`：Command JSON 协议。
- `docs/design/llm.md`：LLM 适配层。
