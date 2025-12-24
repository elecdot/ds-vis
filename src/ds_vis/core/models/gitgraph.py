from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Set

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.base import BaseModel, IdAllocator
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


@dataclass
class GitCommit:
    commit_id: str
    message: str
    parents: List[str] = field(default_factory=list)
    branch: Optional[str] = None


class GitGraphModel(BaseModel):
    """
    简化 Git DAG 教学模型，支持 init/commit/checkout。

    - commit 节点：circle，label=commit_id 短名或 message。
    - branch/HEAD label：rect 形状，使用 SET_POS/SET_LABEL 移动。
    - 不处理 merge/branch 删除，commit id 为递增编号。
    """

    def __init__(
        self, structure_id: str, id_allocator: IdAllocator | None = None
    ) -> None:
        super().__init__(structure_id=structure_id, id_allocator=id_allocator)
        self.commits: Dict[str, GitCommit] = {}
        self.branches: Dict[str, str] = {}  # branch -> commit_id
        self.head: Optional[str] = None  # branch name or detached commit id
        self._commit_order: List[str] = []
        self._branch_set: Set[str] = set()

    @property
    def kind(self) -> str:
        return "git"

    @property
    def node_count(self) -> int:
        return len(self.commits)

    def apply_operation(self, op: str, payload: Mapping[str, object]) -> Timeline:
        if op == "init":
            return self.git_init()
        if op == "commit":
            raw = payload.get("message")
            message = str(raw) if raw is not None else "commit"
            return self.commit(message=message)
        if op == "checkout":
            target = payload.get("target")
            if not isinstance(target, str):
                raise ModelError("checkout requires target branch or commit id")
            return self.checkout(target)
        raise ModelError(f"Unsupported git operation: {op}")

    # ------------------------------------------------------------------ #
    # Ops
    # ------------------------------------------------------------------ #
    def git_init(self) -> Timeline:
        timeline = Timeline()
        self.commits.clear()
        self.branches.clear()
        self.head = "main"
        self._branch_set = {"main"}
        self._commit_order = []

        ops = [
            self._msg("git init"),
            self._create_label_op("branch_main", "main"),
            self._create_label_op("HEAD", "HEAD"),
        ]
        timeline.add_step(AnimationStep(ops=ops, label="Init"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def commit(self, message: str) -> Timeline:
        if self.head is None:
            raise ModelError("HEAD is not set; run git init first")
        current_commit = self._current_commit_id()
        commit_id = self._next_commit_id()
        commit = GitCommit(commit_id=commit_id, message=message, parents=[])
        if current_commit:
            commit.parents.append(current_commit)
        self.commits[commit_id] = commit
        self._commit_order.append(commit_id)
        self.branches[self._current_branch()] = commit_id

        ops: List[AnimationOp] = [
            self._msg(f"commit: {message}"),
        ]
        if current_commit:
            ops.append(self._set_state(current_commit, "highlight"))
        ops.append(self._create_node_op(commit_id, message))
        if current_commit:
            ops.append(self._create_edge_op(current_commit, commit_id))

        # Move branch and HEAD labels to new commit
        branch = self._current_branch()
        branch_label_id = f"branch_{branch}"
        ops.append(self._move_label(branch_label_id, commit_id, branch))
        ops.append(self._move_label("HEAD", commit_id, "HEAD"))
        timeline = Timeline()
        timeline.add_step(AnimationStep(ops=ops, label="Commit"))
        timeline.add_step(
            AnimationStep(
                ops=[self._clear_msg()] + self._restore_states(), label="Restore"
            )
        )
        return timeline

    def checkout(self, target: str) -> Timeline:
        timeline = Timeline()
        ops: List[AnimationOp] = []
        if target in self.branches:
            commit_id = self.branches[target]
            ops.append(self._msg(f"checkout {target}"))
            ops.append(self._move_label("HEAD", commit_id, "HEAD"))
            self.head = target
            timeline.add_step(AnimationStep(ops=ops, label="Checkout branch"))
        elif target in self.commits:
            ops.append(self._msg(f"checkout {target} (detached)"))
            ops.append(self._move_label("HEAD", target, "HEAD"))
            self.head = target  # detached
            timeline.add_step(AnimationStep(ops=ops, label="Checkout detached"))
        else:
            timeline.add_step(AnimationStep(ops=[self._msg("Target not found")]))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

    def export_state(self) -> Mapping[str, object]:
        """
        Export commit messages (in creation order), branch tips, and HEAD target.
        """
        commits = [self.commits[cid].message for cid in self._commit_order]
        return {
            "commits": commits,
            "branches": dict(self.branches),
            "head": self.head,
        }

    def _current_commit_id(self) -> Optional[str]:
        if self.head is None:
            return None
        if self.head in self.branches:
            return self.branches.get(self.head)
        if self.head in self.commits:
            return self.head
        return None

    def _current_branch(self) -> str:
        if self.head in self.branches:
            return str(self.head)
        if self.head in self.commits:
            return "detached"
        # 初始阶段 branch label 仍使用 head 字符串（默认 main）
        return str(self.head)

    def _next_commit_id(self) -> str:
        return f"c{len(self.commits)}"

    # ------------------------------------------------------------------ #
    # Op builders
    # ------------------------------------------------------------------ #
    def _create_node_op(self, node_id: str, message: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_NODE,
            target=node_id,
            data={
                "structure_id": self.structure_id,
                "label": message,
                "shape": "circle",
                "kind": "commit",
            },
        )

    def _create_edge_op(self, parent: str, child: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_EDGE,
            target=self.edge_id("git", parent, child),
            data={
                "structure_id": self.structure_id,
                "from": parent,
                "to": child,
            },
        )

    def _create_label_op(self, target: str, text: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.CREATE_NODE,
            target=target,
            data={
                "structure_id": self.structure_id,
                "label": text,
                "shape": "rect",
                "kind": "label",
            },
        )

    def _move_label(self, label_id: str, commit_id: str, text: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_LABEL,
            target=label_id,
            data={
                "structure_id": self.structure_id,
                "text": text,
                "attach_to": commit_id,
            },
        )

    def _set_state(self, target: str, state: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.SET_STATE,
            target=target,
            data={"structure_id": self.structure_id, "state": state},
        )

    def _restore_states(self) -> List[AnimationOp]:
        return [self._set_state(cid, "normal") for cid in self.commits]

    def _msg(self, text: str) -> AnimationOp:
        return AnimationOp(op=OpCode.SET_MESSAGE, target=None, data={"text": text})

    def _clear_msg(self) -> AnimationOp:
        return AnimationOp(op=OpCode.CLEAR_MESSAGE, target=None, data={})

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def export_state(self) -> Mapping[str, object]:
        return {
            "commits": [
                {
                    "id": commit_id,
                    "message": commit.message,
                    "parents": list(commit.parents),
                    "branch": commit.branch,
                }
                for commit_id, commit in self.commits.items()
            ],
            "branches": dict(self.branches),
            "head": self.head,
        }
