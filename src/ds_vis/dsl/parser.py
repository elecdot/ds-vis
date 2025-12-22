from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command
from ds_vis.persistence.json_io import commands_from_json

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ds_vis.core.scene.scene_graph import SceneGraph

def parse_dsl(text: str) -> List[Command]:
    """
    Minimal DSL parser (v0.1): accepts JSON array of commands.

    This is a placeholder to separate DSL concerns from SceneGraph;
    future versions can replace the JSON branch with real syntax parsing.
    """
    text = text.strip()
    if not text:
        return []

    # v0.1: accept JSON as DSL input for compatibility
    try:
        return commands_from_json(text)
    except CommandError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise CommandError(f"Failed to parse DSL input: {exc}") from exc


def run_commands(commands: Iterable[Command], scene_graph: "SceneGraph") -> None:
    """
    Helper to apply a sequence of commands to a SceneGraph.
    """
    for cmd in commands:
        scene_graph.apply_command(cmd)
