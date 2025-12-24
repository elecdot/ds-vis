---
bound_phase: P0.7
version: v0.4
status: Active
last_updated: 2025-12-24
---

# JSON 持久化协议

本文件说明当前阶段的场景级 JSON 序列化协议、验证规则与布局处理。

## 1. 场景级持久化 (v0.4)
不同于早期的单条命令序列化，现在的持久化关注**场景状态**。
- **导出**：将当前场景中所有结构的创建指令及后续操作序列化为 JSON。
- **导入**：清空当前场景，并按 JSON 中的指令序列重建所有结构。

## 2. 数据格式
外层为 JSON 数组，每个元素表示一条 `Command`。
```json
[
  {
    "structure_id": "L1",
    "type": "CREATE_STRUCTURE",
    "payload": {
      "kind": "list",
      "values": [1, 2]
    }
  },
  {
    "structure_id": "L1",
    "type": "INSERT",
    "payload": {
      "kind": "list",
      "index": 1,
      "value": 3
    }
  }
]
```

## 3. 布局隔离与过滤
在导入导出过程中，系统会自动处理不同结构间的布局干扰：
- **过滤机制**：导出时会根据结构类型（如 Git、Huffman）过滤掉不属于该结构的布局指令，确保重新加载后布局依然正确。
- **坐标恢复**：`CREATE_STRUCTURE` 负载中可包含初始状态，后续通过 `SET_POS` 等 Ops 恢复视觉位置。

## 4. 校验规则
- 解析由 `persistence/json_io.commands_from_json` 完成。
- 验证：
  - `structure_id`/`type`/`payload` 必填。
  - `SCHEMA_REGISTRY` 根据 `(CommandType, kind)` 执行字段校验。
  - 导入时如果缺少 `kind` 且结构尚未创建，会抛出 `CommandError`。

## 5. UI 集成
- **File -> Import Scene**：从文件加载 JSON 并重建场景。
- **File -> Export Scene**：将当前场景状态保存为 JSON 文件。

## 6. 关联文件
- `src/ds_vis/persistence/json_io.py` — 核心实现。
- `src/ds_vis/ui/main_window.py` — UI 菜单绑定。
