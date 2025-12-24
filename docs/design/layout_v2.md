---
bound_phase: P0.8
version: v2.0
status: Draft
last_updated: 2025-12-24
---

# LAYOUT V2 — 拓扑感知与无状态布局重构

## 1. 背景与动机
当前 P0.7 的布局引擎（Layout Engine）存在以下核心缺陷：
- **信息降级**：通过解析指令流（Ops Sniffing）逆向推断拓扑，脆弱且低效。
- **状态耦合**：引擎内部维护状态，不支持 seek、倒播或任意时刻的重排。
- **算法简陋**：树布局采用固定宽度平分法，导致深度增加时节点重叠。
- **个性化不足**：难以支持 Huffman（双区）、Git（多 Lane）等复杂结构的个性化需求。

## 2. 核心设计原则
- **拓扑感知 (Topology-Aware)**：Layout 直接访问 Model 的逻辑结构，而非猜指令。
- **无状态计算 (Stateless Calculation)**：布局计算应为纯函数 `f(Snapshot) -> Positions`。
- **声明式提示 (Layout Hints)**：Model 通过 Ops 携带布局提示，引导引擎决策。
- **算法升级**：引入 Buchheim / Reingold-Tilford 等专业树布局算法。

## 3. 架构组件

### 3.1 `Layoutable` 协议
Model 需实现此协议以暴露拓扑信息：
```python
class Layoutable(Protocol):
    def get_topology_snapshot(self) -> TopologySnapshot:
        ...
```
`TopologySnapshot` 包含：
- 节点列表及其属性（kind, label, hints）。
- 边列表（src, dst, type）。
- 容器关系（parent_container, children）。

### 3.2 `LayoutEngine V2`
接口变更：
```python
class LayoutEngineV2(Protocol):
    def compute_layout(self, snapshot: TopologySnapshot, config: LayoutConfig) -> Dict[str, Tuple[float, float]]:
        ...
```

### 3.3 `SceneGraph` 协调器
- 负责从 Model 获取 Snapshot。
- 调用对应的 `LayoutEngine` 计算坐标。
- 对比新旧坐标，自动生成 `SET_POS` 指令并注入 `Timeline`。

## 4. 关键算法：Buchheim 树布局
针对树结构重叠问题，引入 Buchheim 算法：
- **第一遍遍历**：初步分配相对坐标，处理子树间的间距（Modifier）。
- **第二遍遍历**：累加 Modifier，计算绝对坐标。
- **优势**：节点间距最小化，绝不重叠，支持变宽节点。

## 5. 混合布局支持 (Huffman/Git)
- **Zone-based Layout**：支持将画布划分为多个区域（如 Huffman 的 Queue 区和 Tree 区）。
- **Lane-based Layout**：Git 专用，支持多分支并行 Lane 布局。

## 6. 迁移路径
1. 定义 `Layoutable` 和 `TopologySnapshot`。
2. 重构 `BaseModel` 和现有模型以支持 `Layoutable`。
3. 实现 `StatelessLayoutManager` 替代现有的 `apply_layout` 逻辑。
4. 逐步替换 `TreeLayoutEngine` 为 Buchheim 实现。

## 7. 预期效果
- 彻底解决树节点重叠问题。
- 天然支持动画回放、跳转（Seek）。
- 极大简化新数据结构的布局开发工作。
