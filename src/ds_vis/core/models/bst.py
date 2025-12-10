from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from ds_vis.core.ops import AnimationOp


@dataclass
class BstNode:
    """Logical node for a binary search tree model."""

    key: int  # Phase 0: keep it simple, refine later
    left: Optional["BstNode"] = None
    right: Optional["BstNode"] = None


@dataclass
class BstModel:
    """
    Binary Search Tree model.

    This class owns the logical structure and exposes operations that
    return AnimationOps sequences for visualization.

    Implementation will be provided in later phases.
    """

    root: Optional[BstNode] = None

    def insert(self, key: int) -> Sequence[AnimationOp]:
        """Insert a key into the BST and return the animation ops."""
        # TODO: implement in later phase
        return []

    def delete(self, key: int) -> Sequence[AnimationOp]:
        """Delete a key from the BST and return the animation ops."""
        # TODO: implement in later phase
        return []

    def search(self, key: int) -> Sequence[AnimationOp]:
        """Search for a key in the BST and return the animation ops."""
        # TODO: implement in later phase
        return []
