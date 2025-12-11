"""
SceneGraph and command layer.

This is the central entry point for high-level operations, coming from
UI / DSL / persistence, and routing them to the appropriate models.
"""

from __future__ import annotations

from .command import Command, CommandType
from .scene_graph import SceneGraph

__all__ = ["Command", "CommandType", "SceneGraph"]
