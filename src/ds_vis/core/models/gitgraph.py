from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Set

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
        if op == "create":
            return self.create(payload)
        if op == "commit":
            raw = payload.get("message")
            message = str(raw) if raw is not None else "commit"
            return self.commit(message=message)
        if op == "checkout":
            target = payload.get("target")
            if not isinstance(target, str):
                raise ModelError("checkout requires target branch or commit id")
            return self.checkout(target)
        if op == "delete_all":
            return self.delete_all()
        raise ModelError(f"Unsupported git operation: {op}")

    # ------------------------------------------------------------------ #
    # Ops
    # ------------------------------------------------------------------ #
    def create(self, payload: Mapping[str, Any]) -> Timeline:
        """
        Initialize or restore git state.
        """
        if "commits" in payload or "branches" in payload:
            return self.restore(payload)
        return self.git_init()

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

    def delete_all(self) -> Timeline:
        """Delete all commits and labels."""
        timeline = Timeline()
        ops: List[AnimationOp] = [self._msg("Deleting all git structures")]

        # Delete labels (HEAD and branches)
        ops.append(self._delete_node_op("HEAD"))
        for bname in self.branches:
            ops.append(self._delete_node_op(f"branch_{bname}"))

        # Delete commits
        for cid in self.commits:
            ops.append(self._delete_node_op(cid))

        self.commits.clear()
        self.branches.clear()
        self.head = None
        self._branch_set.clear()
        self._commit_order.clear()

        timeline.add_step(AnimationStep(ops=ops, label="Delete all"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore"))
        return timeline

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

    def _delete_node_op(self, node_id: str) -> AnimationOp:
        return AnimationOp(
            op=OpCode.DELETE_NODE,
            target=node_id,
            data={"structure_id": self.structure_id},
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

    def restore(self, state: Mapping[str, Any]) -> Timeline:
        """
        Restore git state from a snapshot.
        """
        timeline = Timeline()
        self.commits.clear()
        self.branches.clear()
        self._commit_order.clear()
        self._branch_set.clear()

        commits_data = state.get("commits", [])
        branches_data = state.get("branches", {})
        head_data = state.get("head")

        ops = [self._msg("Restoring git state")]

        # 1. Restore commits
        for c_data in commits_data:
            cid = c_data["id"]
            msg = c_data["message"]
            parents = c_data["parents"]
            branch = c_data.get("branch")
            commit = GitCommit(
                commit_id=cid, message=msg, parents=parents, branch=branch
            )
            self.commits[cid] = commit
            self._commit_order.append(cid)
            ops.append(self._create_node_op(cid, msg))
            for p in parents:
                ops.append(self._create_edge_op(p, cid))

        # 2. Restore branches
        for bname, cid in branches_data.items():
            self.branches[bname] = cid
            self._branch_set.add(bname)
            ops.append(self._create_label_op(f"branch_{bname}", bname))
            ops.append(self._move_label(f"branch_{bname}", cid, bname))

        # 3. Restore HEAD
        self.head = head_data
        ops.append(self._create_label_op("HEAD", "HEAD"))
        if head_data:
            if head_data in self.branches:
                target_cid = self.branches[head_data]
                ops.append(self._move_label("HEAD", target_cid, "HEAD"))
            elif head_data in self.commits:
                ops.append(self._move_label("HEAD", head_data, "HEAD"))

        timeline.add_step(AnimationStep(ops=ops, label="Restore"))
        timeline.add_step(AnimationStep(ops=[self._clear_msg()], label="Restore end"))
        return timeline

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
