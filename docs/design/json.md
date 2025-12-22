---
bound_phase: P0.7
version: v0.2
status: Draft
last_updated: 2025-12-22
---

# Command JSON 协议（持久化占位）

本文件说明当前阶段的最小 JSON Command 载入/导出协议、验证规则与已知限制。该协议用于 DSL 占位输入、CLI/UI 开发钩子，以及后续 persistence 基础。

## 1. 数据格式
- 外层：JSON 数组，每个元素表示一条命令。
- 每条命令字段：
  - `structure_id` (string) — 目标结构实例 ID。
  - `type` (string) — `CommandType` 的名字，例如 `CREATE_STRUCTURE`、`INSERT`、`DELETE_STRUCTURE` 等。
  - `payload` (object) — 具体参数，至少包含 `kind`（string），其余字段依赖 `kind` 与 `type`。

示例：
```json
[
  {"structure_id": "list-1", "type": "CREATE_STRUCTURE", "payload": {"kind": "list", "values": [1,2]}},
  {"structure_id": "list-1", "type": "INSERT", "payload": {"kind": "list", "index": 1, "value": 3}}
]
```

## 2. 校验规则
- 解析由 `persistence/json_io.commands_from_json` 完成。
- 验证：
  - JSON 必须是数组；每个元素必须是对象。
  - `structure_id`/`type`/`payload` 必填且类型正确。
  - `type` 必须是已注册的 `CommandType`；`kind` 必须是字符串。
  - `SCHEMA_REGISTRY` 根据 `(CommandType, kind)` 执行字段校验（必填/可选/额外字段禁用等）；所有错误抛 `CommandError`。
- 导出：`commands_to_json` 将 `Command` 列表序列化为相同结构，不做额外压缩或排序。

## 3. 当前支持的命令/结构（P0.7）
- kind：`list` / `seqlist` / `stack` / `bst` / `huffman` / `git`（后两者占位）。
- 命令：`CREATE_STRUCTURE`（可含 `values`）、`DELETE_STRUCTURE`、`DELETE_NODE`（index 或 value）、`INSERT`（index/value）、`SEARCH`（index 或 value）、`UPDATE`（index 或 value + new_value）。
- 新结构需在 `command_schema.register_command` 与 `register_model_factory` 完成注册。

## 4. 假设与限制
- 不支持注释/尾逗号；严格 JSON。
- 不支持流式/分块输入；需一次性加载完整数组。
- 未设计版本字段；未来协议演进需在外层加版本或头信息。
- 执行模型为同步阻塞；未区分事务/批次成功与否（错误即抛）。
- 未内置 seek/undo；重放需自行管理命令序列。

## 5. 后续期望
- 增加协议版本字段与向后兼容策略。
- 提供增量/流式加载（生成器）与分批校验。
- 提供“预检”模式：仅校验不执行，返回错误列表。
- 支持非 JSON DSL 自动编译为该结构，作为通用交换格式。

## 6. 文件读写（v0.2 增量）
- `commands_from_json(text: str) -> list[Command]`：字符串解析与校验。
- `commands_to_json(commands: Iterable[Command]) -> str`：序列化为字符串。
- `load_commands_from_file(path)` / `save_commands_to_file(commands, path)`：文件级别读写，IO/校验错误抛 `CommandError`。

## 7. 关联文件
- `src/ds_vis/persistence/json_io.py` — 解析/导出与校验实现。
- `docs/design/dsl.md` — DSL 占位与未来语法方向。
- `docs/design/llm.md` — LLM 适配层（自然语言转 DSL/JSON）。
