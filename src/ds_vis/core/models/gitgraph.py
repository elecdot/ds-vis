from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from ds_vis.core.ops import AnimationOp


@dataclass
class CommitNode:
    """
    Simplified commit node for Git teaching visualization.

    Does NOT represent file contents or diffs, only the commit graph structure.
    """

    id: str
    parents: List[str] = field(default_factory=list)
    message: str = ""
    branch_labels: List[str] = field(default_factory=list)


@dataclass
class GitGraphModel:
    """
    Simplified Git commit graph model for teaching.

    Supports virtual operations such as init/commit/branch/checkout/merge.
    """

    commits: Dict[str, CommitNode] = field(default_factory=dict)
    head: Optional[str] = None
    head_ref: Optional[str] = None  # e.g. branch name, or None for detached
    branches: Dict[str, str] = field(default_factory=dict)  # branch -> commit id

    def init_repo(self) -> Sequence[AnimationOp]:
        """Initialize an empty repository. To be implemented later."""
        return []

    def commit(self, message: str) -> Sequence[AnimationOp]:
        """Create a new commit on the current HEAD. To be implemented later."""
        return []

    def branch(self, name: str) -> Sequence[AnimationOp]:
        """Create a new branch pointing to the current commit. To be implemented later."""
        return []

    def checkout(self, target: str) -> Sequence[AnimationOp]:
        """Checkout a branch or commit by name/id. To be implemented later."""
        return []

    def merge(self, branch: str) -> Sequence[AnimationOp]:
        """Create a simplified merge commit. To be implemented later."""
        return []
