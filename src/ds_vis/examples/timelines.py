# src/ds_vis/examples/timelines.py

from __future__ import annotations

from ds_vis.core.ops import (
    Timeline,
    AnimationStep,
    AnimationOp,
    OpCode,
)


def bst_insert_7_into_root_5() -> Timeline:
    """
    Example: insert key=7 into a BST where the only node is root=5.

    Initial state (conceptually):
      - structure_id: "bst_1"
      - node_5 exists and is the root (already created in the scene)

    This example focuses purely on the *animation semantics*,
    not on the internal tree invariants.
    """

    timeline = Timeline()

    # Step 1: highlight root and explain comparison
    step1 = AnimationStep(
        duration_ms=400,
        label="比较根结点 5 与待插入值 7",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_5",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "当前结点 5：7 > 5，前往右子树"},
            ),
        ],
    )
    timeline.add_step(step1)

    # Step 2: 右子树为空，准备在此处创建新结点
    step2 = AnimationStep(
        duration_ms=400,
        label="右子树为空，在此处插入新结点 7",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_5",
                data={"state": "secondary"},  # 仍然显示路径中的结点，但不是当前焦点
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "右子树为空，在结点 5 的右侧创建新结点 7"},
            ),
        ],
    )
    timeline.add_step(step2)

    # Step 3: 创建 node_7 和从 node_5 到 node_7 的边
    step3 = AnimationStep(
        duration_ms=400,
        label="创建结点 7 并连接到 5 的右子结点",
        ops=[
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target="node_7",
                data={
                    "structure_id": "bst_1",
                    "kind": "bst_node",
                    "label": "7",
                    "meta": {"key": 7},
                },
            ),
            AnimationOp(
                op=OpCode.CREATE_EDGE,
                target="edge_5_7",
                data={
                    "structure_id": "bst_1",
                    "from": "node_5",
                    "to": "node_7",
                    "directed": True,
                    "label": "right",
                },
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_7",
                data={"state": "active"},
            ),
        ],
    )
    timeline.add_step(step3)

    # Step 4: 收尾，将所有结点恢复为 normal，清理提示
    step4 = AnimationStep(
        duration_ms=300,
        label="插入完成",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_5",
                data={"state": "normal"},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_7",
                data={"state": "normal"},
            ),
            AnimationOp(
                op=OpCode.CLEAR_MESSAGE,
                target=None,
                data={},
            ),
        ],
    )
    timeline.add_step(step4)

    return timeline

def avl_single_left_rotation_example() -> Timeline:
    """
    Example: single left rotation at node_x with right child node_y.

    This does NOT modify real tree pointers; it only describes
    how the visualization should reflect the rotation.
    """

    timeline = Timeline()

    # Step 1: 标记失衡的结点 x
    step1 = AnimationStep(
        duration_ms=400,
        label="检测到结点 x 失衡（右子树过高）",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_x",
                data={"state": "error"},  # 用 error 或特殊颜色表示失衡
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "结点 x 失衡：右子树过高，需要左旋"},
            ),
        ],
    )
    timeline.add_step(step1)

    # Step 2: 高亮旋转枢轴 y
    step2 = AnimationStep(
        duration_ms=400,
        label="选择右子结点 y 作为左旋枢轴",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_y",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_x",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "围绕 x 对 y 进行左旋：y 将成为新的子树根"},
            ),
        ],
    )
    timeline.add_step(step2)

    # Step 3: 删除旧边，创建新边（逻辑上表现旋转）
    step3 = AnimationStep(
        duration_ms=500,
        label="更新指针结构（逻辑左旋）",
        ops=[
            # 删除旧边 x -> y
            AnimationOp(
                op=OpCode.DELETE_EDGE,
                target="edge_x_y",
                data={},
            ),
            # 示例：假设 y 的左子为 B：edge_y_B
            # 旋转后 B 将成为 x 的右子
            AnimationOp(
                op=OpCode.DELETE_EDGE,
                target="edge_y_B",
                data={},
            ),
            AnimationOp(
                op=OpCode.CREATE_EDGE,
                target="edge_x_B",
                data={
                    "structure_id": "avl_1",
                    "from": "node_x",
                    "to": "node_B",
                    "directed": True,
                    "label": "right",
                },
            ),
            # y 成为子树新根：父结点（如 parent）指向 y，这里只演示局部
            AnimationOp(
                op=OpCode.CREATE_EDGE,
                target="edge_y_x",
                data={
                    "structure_id": "avl_1",
                    "from": "node_y",
                    "to": "node_x",
                    "directed": True,
                    "label": "left",
                },
            ),
        ],
    )
    timeline.add_step(step3)

    # Step 4: 恢复所有结点状态为 normal，清理提示
    step4 = AnimationStep(
        duration_ms=300,
        label="左旋完成，子树重新平衡",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_x",
                data={"state": "normal"},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_y",
                data={"state": "normal"},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="node_B",
                data={"state": "normal"},
            ),
            AnimationOp(
                op=OpCode.CLEAR_MESSAGE,
                target=None,
                data={},
            ),
        ],
    )
    timeline.add_step(step4)

    return timeline

def git_commit_example() -> Timeline:
    """
    Example: virtual `git commit -m "add feature"` on repo_1.

    Assumes:
      - commit node 'c1' exists,
      - branch_main and head_label are already in the scene.
    """

    timeline = Timeline()

    # Step 1: 高亮当前 HEAD 所在提交
    step1 = AnimationStep(
        duration_ms=400,
        label="定位当前 HEAD 所在提交",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="c1",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="head_label",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "HEAD 指向提交 c1，执行 git commit 生成新提交"},
            ),
        ],
    )
    timeline.add_step(step1)

    # Step 2: 创建新提交 c2，并连接 c1 -> c2
    step2 = AnimationStep(
        duration_ms=500,
        label="创建新提交 c2",
        ops=[
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target="c2",
                data={
                    "structure_id": "repo_1",
                    "kind": "git_commit",
                    "label": "c2",
                    "meta": {"message": "add feature"},
                },
            ),
            AnimationOp(
                op=OpCode.CREATE_EDGE,
                target="edge_c1_c2",
                data={
                    "structure_id": "repo_1",
                    "from": "c1",
                    "to": "c2",
                    "directed": True,
                },
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="c2",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "新提交 c2 追加在 c1 之后"},
            ),
        ],
    )
    timeline.add_step(step2)

    # Step 3: 更新 main 分支 label 和 HEAD label 指向 c2
    step3 = AnimationStep(
        duration_ms=400,
        label="更新 main 分支和 HEAD 到新提交 c2",
        ops=[
            AnimationOp(
                op=OpCode.SET_LABEL,
                target="branch_main",
                data={"text": "main -> c2"},
            ),
            AnimationOp(
                op=OpCode.SET_LABEL,
                target="head_label",
                data={"text": "HEAD -> main"},
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="c1",
                data={"state": "normal"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "git commit 完成：HEAD 与 main 一起移动到 c2"},
            ),
        ],
    )
    timeline.add_step(step3)

    return timeline

def git_branch_example() -> Timeline:
    """
    Example: virtual `git branch feature` at commit c2.
    """

    timeline = Timeline()

    step1 = AnimationStep(
        duration_ms=400,
        label="在当前提交 c2 创建分支 feature",
        ops=[
            AnimationOp(
                op=OpCode.SET_STATE,
                target="c2",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "git branch feature：创建指向 c2 的新分支"},
            ),
        ],
    )
    timeline.add_step(step1)

    step2 = AnimationStep(
        duration_ms=400,
        label="展示新分支标签 feature",
        ops=[
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target="branch_feature",
                data={
                    "structure_id": "repo_1",
                    "kind": "git_branch_label",
                    "label": "feature",
                    "meta": {"commit": "c2"},
                },
            ),
            AnimationOp(
                op=OpCode.SET_STATE,
                target="branch_feature",
                data={"state": "active"},
            ),
            AnimationOp(
                op=OpCode.SET_MESSAGE,
                target=None,
                data={"text": "新分支 feature 现在也指向 c2"},
            ),
        ],
    )
    timeline.add_step(step2)

    return timeline