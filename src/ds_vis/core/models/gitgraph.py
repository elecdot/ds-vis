from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ds_vis.core.ops import Timeline


@dataclass
class CommitNode:
    """
    Simplified commit node for Git teaching visualization.

    Represents only the commit graph structure and labels, not file contents.
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

    Timelines produced here should be structural only (no SET_POS).
    """

    commits: Dict[str, CommitNode] = field(default_factory=dict)
    head: Optional[str] = None             # current commit id
    head_ref: Optional[str] = None         # branch name or None for detached HEAD
    branches: Dict[str, str] = field(default_factory=dict)  # branch -> commit id

    def init_repo(self) -> Timeline:
        """Initialize an empty repository (structural Timeline stub)."""
        return Timeline()

    def commit(self, message: str) -> Timeline:
        """Create a new commit on the current HEAD (structural Timeline stub)."""
        return Timeline()

    def branch(self, name: str) -> Timeline:
        """Create a new branch pointing to the current commit (structural Timeline stub)."""
        return Timeline()

    def checkout(self, target: str) -> Timeline:
        """Checkout a branch or commit by name/id (structural Timeline stub)."""
        return Timeline()

    def merge(self, branch: str) -> Timeline:
        """Create a simplified merge commit (structural Timeline stub)."""
        return Timeline()
