# Plan

面向 P0.8 及后续，构建可快速迭代的基础设施与指南，支撑 Coding Agent 按指令高效扩展（AVL/DSL/LLM 等）。

## Milestones

### Milestone 1：Layout 抽象与策略化
- 定义 Layout 接口与策略选择（线性/树/DAG 占位），保留 SimpleLayout 兼容层。
- 提供重建/无状态模式入口，便于 seek/倒播/重排 timeline。
- 测试：接口单测 + SceneGraph 集成冒烟。

### Milestone 2：Renderer 配置化与消息策略
- 引入样式/动画参数配置（颜色、尺寸、帧率/缓动占位），默认值与当前视觉一致。
- 消息策略：固定 HUD 文本可禁用，预留锚定节点接口占位。
- 测试：属性应用、消息显示/清除。

### Milestone 3：动画/状态规范文档化
- 在 `animation.md` / `model.md` 补充状态值语义表、消息使用约定、微步骤拆解模板（新结构开发指北）。
- 同步 registry 版本。

### Milestone 4：SceneGraph/command_schema 可维护性
- 重构 schema 验证为命名函数，去除 lambda 生成器抛异常技巧。
- 预留结构注册模板/工厂，便于新增模型命令映射。
- 测试：命令校验回归。

### Milestone 5：DSL/LLM 入口 + Persistence
- 定义最小 JSON Command 协议（导入/导出）作为 persistence 入口。
- 定义 DSL 语法（可编译为 Command 列表）与解析 stub；UI/CLI 入口钩子。
- LLM 适配占位：接口定义（自然语言 -> DSL/Command），不实现模型调用。
- 测试：DSL 解析正/误用例，JSON 导入/导出往返测试。

### Milestone 6：树形模型起步（AVL/BST）
- 选 AVL 或 BST 做最小骨架：create/insert（或旋转 stub）+ 微步骤规范。
- Tree/DAG 布局占位参与 SET_POS 注入（可用简单层次布局或固定坐标）。
- 测试：Model 单测、SceneGraph 路由、Renderer 属性断言；旋转可先 xfail 锁定预期。

### Milestone 7：全流程开发指南
- 编写“从需求到交付”指南：选一个新模型（或命令）为例，涵盖：
  - 需求→测试（TDD）
  - Model 微步骤拆解与颜色/消息约定
  - Layout/Renderer 接入（使用配置/策略）
  - SceneGraph/命令注册
  - DSL/JSON persistence 流
  - Dev/UI 验收与 CI 检查

## 顺序建议
1. Milestone 1 & 2 小步并行：Layout 抽象 + Renderer 参数化（保持兼容）。
2. Milestone 3 文档规范同步。
3. Milestone 4 精简 command_schema。
4. Milestone 5 建立 DSL/JSON/persistence 骨架 + UI/CLI 钩子。
5. Milestone 6 启动树形模型，验证基建。
6. Milestone 7 输出全流程指南，固化实践。

## 风险与缓解
- Layout 抽象影响现有 dev hook：保留 SimpleLayout 兼容层，先提供线性策略默认。
- Renderer 参数化可能改视觉：默认配置与现状一致，配置为可选。
- DSL/LLM/JSON 范围过大：先落地最小 JSON 协议 + DSL 编译为 Command，LLM 仅留接口。
- 树形模型缺规范：先文档化旋转微步骤，必要时 xfail 锁定。
