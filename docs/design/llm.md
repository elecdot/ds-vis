---
bound_phase: P0.7
version: v0.1
status: Draft
last_updated: 2025-12-24
---

# LLM 适配设计（占位）

本文件描述当前阶段的 LLM 适配层接口、假设与后续方向。现阶段仅提供本地可插拔接口与占位实现，不调用任何真实 LLM。

## 1. 目标与范围
- 目标：定义“自然语言 → DSL/JSON → Command” 的最小接口，为未来 LLM 集成留好挂载点。
- 范围：`LLMClient` 协议、`LLMAdapter` 桥接、prompt 前缀配置；不涉及模型选择/对话存储/安全过滤。

## 2. 当前实现（v0.1）
- 协议：`LLMClient.generate(prompt: str) -> str`，需返回可被 DSL 解析的文本。
- 适配器：`LLMAdapter(client=None, prompt_prefix="")`
  - `to_dsl(request)`：无 client 时直接返回输入；有 client 时拼接前缀后调用 `generate`。
  - `to_commands(request)`：`to_dsl` 后调用 `parse_dsl`（当前 DSL 仍是 JSON 占位）。
- 默认行为：未注入 client 时，传入的请求被当作 DSL/JSON 直接解析。

## 3. 假设与限制
- 无外部网络/模型调用；不含鉴权或速率控制。
- 无对 prompt/回复的安全过滤；需在接入真实 LLM 时补充。
- 不维护对话状态；每次调用为单轮请求。
- DSL 解析能力受限于当前占位（仅 JSON）；复杂自然语言需求无法直接满足。

## 4. 未来方向
- 支持多轮对话与上下文记忆；可插拔 System Prompt 模板。
- 安全策略：注入 schema 校验后的“拒绝/修正”回路，避免危险/无效命令。
- 提供 provider 适配器（OpenAI/Azure/local 模型等），并隔离网络依赖。
- UI/CLI 集成：交互式对话窗、生成结果预览与人工确认。
- 与真实 DSL 语法结合：LLM 输出结构化 DSL 而非裸 JSON。

## 5. 关联文件
- `src/ds_vis/llm/adapter.py` — 接口与占位实现。
- `docs/design/dsl.md` — DSL 占位与未来语法。
- `docs/design/json.md` — Command JSON 交换格式。
