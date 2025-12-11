import pytest

from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.scene_graph import SceneGraph


@pytest.fixture
def scene_graph():
    """Returns a fresh SceneGraph instance for each test."""
    return SceneGraph()

@pytest.fixture
def create_cmd_factory():
    """Helper to create commands easily."""
    def _create(structure_id: str, cmd_type: CommandType, **payload):
        return Command(structure_id=structure_id, type=cmd_type, payload=payload)
    return _create
