from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ds_vis.core.ops import Timeline


@dataclass
class BstNode:
    """
    Logical node for a binary search tree model.

    Domain-only representation; no rendering or layout concerns here.
    """

    key: int  # Phase 1: keep simple (int keys). Can be generalized later.
    left: Optional["BstNode"] = None
    right: Optional["BstNode"] = None


@dataclass
class BstModel:
    """
    Binary Search Tree model.

    This class owns the logical structure and exposes operations that
    return Timelines describing structural and visual-state changes.

    IMPORTANT:
    - Timelines produced here should NOT contain layout-specific ops (e.g. SET_POS).
    - Layout is handled by the layout engine based on the structure's shape.
    """

    root: Optional[BstNode] = None

    def insert(self, key: int) -> Timeline:
        """
        Insert a key into the BST and return a structural Timeline.

        Phase 1: stub only; implementation will be provided in later phases.
        """
        return Timeline()

    def delete(self, key: int) -> Timeline:
        """
        Delete a key from the BST and return a structural Timeline.
        """
        return Timeline()

    def search(self, key: int) -> Timeline:
        """
        Search for a key in the BST and return a structural Timeline.

        Even for 'read-only' operations, we return a Timeline so the caller
        can animate the traversal path.
        """
        return Timeline()
