---
bound_phase: P0.7
version: v0.2
status: Active
last_updated: 2025-12-24
---

# Quickstart — 快速上手指南

本指南将帮助你快速搭建环境、运行项目并了解核心交互流程。

## 1. 环境搭建

本项目使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理。

```bash
# 1. 克隆仓库
git clone https://github.com/elecdot/ds-vis.git
cd ds-vis

# 2. 同步依赖 (自动创建虚拟环境)
uv sync
```

## 2. 运行应用

启动桌面端可视化窗口：

```bash
uv run python -m ds_vis.ui.main_window
```

## 3. 核心交互流程

### 3.1 使用 Interactive DSL (推荐)
在主界面右侧控制面板点击 **"Interactive DSL"** 按钮，你可以直接输入文本指令来操控场景。

**常用指令示例：**
```python
# 创建并初始化
list L1 = [1, 2, 3]; 
bst B1 = [10, 5, 15];

# 结构操作
insert L1 1 99;    # 在 L1 的索引 1 插入 99
push S1 10;        # 如果 S1 是栈，执行入栈
search B1 5;       # 在二叉树中搜索 5

# 注释支持
# 这是一个注释，会被解析器忽略
```

### 3.2 场景持久化
- **导出**：点击菜单栏 \`File -> Export Scene\`，将当前场景的所有结构和操作序列保存为 JSON 文件。
- **导入**：点击 \`File -> Import Scene\`，加载 JSON 文件以重建整个场景。

## 4. 开发者工作流 (TDD)

如果你想为项目贡献代码（如新增一个数据结构模型），请遵循以下流程：

1. **定义 Schema**：在 \`src/ds_vis/core/scene/command_schema.py\` 中注册新命令。
2. **编写测试**：在 \`tests/core/models/\` 下编写针对新模型的单元测试。
3. **实现模型**：在 \`src/ds_vis/core/models/\` 下实现逻辑，并生成 \`AnimationOps\`。
4. **运行验证**：
   \`\`\`bash
   uv run pytest tests/core/models/test_your_model.py
   uv run ruff check src
   uv run mypy src
   \`\`\`

## 5. 架构简述

DS-Vis 采用严格的**三层分离**架构，确保逻辑与表现解耦：

1. **Model 层** (\`src/ds_vis/core/models/\`)：负责逻辑拓扑，生成抽象的 \`AnimationOps\`（如 \`CREATE_NODE\`, \`SET_LABEL\`）。
2. **Layout 层** (\`src/ds_vis/core/layout/\`)：负责几何计算，为节点注入 \`SET_POS\` 指令。
3. **Renderer 层** (\`src/ds_vis/renderers/\`)：消费指令序列，执行具体的绘图与动画插值。

> 更多详细设计请参考 [docs/design/architecture.md](design/architecture.md)。

---
**下一站导览：** [项目需求定义](design/requirements.md)
