# Data Structure Visualizer (DS-Vis)

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个面向教学的数据结构与算法可视化工具，基于 Python + PySide6 构建。本项目不仅提供直观的算法演示，更核心的是构建了一个**可复用的动画引擎**：数据结构模型 → 抽象动画指令 (AnimationOps) → 可插拔渲染器。

> 本项目的文档你可以访问[mkdocs site (github.io)](https://elecdot.github.io/ds-vis/)查看

---

## 🚀 核心特性

- **多数据结构支持**：
  - **线性表**：List (链表), Seqlist (顺序表), Stack (栈)。
  - **树形结构**：BST (二叉搜索树), Huffman Tree (赫夫曼树 - 建设中)。
  - **图与版本控制**：Git Commit Graph (Git 提交图可视化)。
- **交互式 DSL (领域专用语言)**：
  - 支持通过自然指令操控数据结构，如 `list L1 = [1, 2, 3]; insert L1 1 99`。
  - **Late-binding**：指令可自动识别场景中已存在的结构类型。
  - 支持注释 (`#`) 与多行脚本。
- **场景持久化**：
  - 支持完整的场景导入与导出 (JSON 格式)。
  - 自动处理不同结构间的布局隔离。
- **精细动画引擎**：
  - L2 级微步骤拆解，支持消息提示、节点高亮、边状态追踪。
  - 自动布局计算，支持多结构同屏展示。

---

## 🛠️ 技术栈

- **语言**: Python 3.11+
- **依赖管理**: [uv](https://github.com/astral-sh/uv)
- **GUI 框架**: PySide6 (Qt for Python)
- **测试**: pytest + pytest-qt
- **规范**: Ruff (Linting), Mypy (Type Check)

---

## 📦 快速开始

详情请参阅 [Quickstart 指南](docs/quickstart.md)。

### 1. 安装环境
本项目推荐使用 `uv` 进行依赖管理：

```bash
# 安装 uv (如果尚未安装)
curl -LsSf https://astral-sh/uv/install.sh | sh

# 同步依赖并创建虚拟环境
uv sync
```

### 2. 运行应用
启动主可视化窗口：

```bash
uv run python -m ds_vis.ui.main_window
```

### 3. 使用 DSL
在 UI 界面点击 **"Interactive DSL"** 按钮，输入以下指令尝试：
```python
list L1 = [10, 20]; # 创建列表
insert L1 1 15;     # 在索引1插入15
bst B1 = [5, 3, 7]; # 创建二叉树
search B1 3;        # 搜索节点
```

---

## 📂 项目结构

```text
.
├── docs/               # 设计与工程文档 (Registry & SSOT)
├── src/ds_vis/
│   ├── core/           # 引擎核心
│   │   ├── models/     # 数据结构逻辑 (Model 层)
│   │   ├── layout/     # 布局算法 (Layout 层)
│   │   ├── ops/        # 动画指令协议 (Ops 层)
│   │   └── scene/      # 场景图与指令分发 (SceneGraph)
│   ├── dsl/            # DSL 解析器与 CLI
│   ├── persistence/    # JSON 导入导出
│   ├── renderers/      # PySide6 渲染器实现
│   └── ui/             # 桌面端 UI 逻辑
├── tests/              # 完整的单元测试与 UI 测试
└── pyproject.toml      # 项目配置
```

---

## 🧪 开发与测试

我们遵循 TDD (测试驱动开发) 流程，确保每一项指令和模型逻辑都经过验证。

```bash
# 运行全量测试
uv run pytest

# 代码规范检查
uv run ruff check src tests

# 类型检查
uv run mypy src
```

---

## 📐 架构原则

本项目严格遵守以下三层分离原则：
1. **Model 层**：仅负责逻辑拓扑，不感知坐标与 UI。
2. **Layout 层**：负责几何计算，将拓扑转换为坐标。
3. **Renderer 层**：负责视觉呈现，消费统一的 `AnimationOps` 指令。

详细设计请参考 [docs/design/architecture.md](docs/design/architecture.md)。

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源。
