import pytest

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.command_schema import MODEL_OP_REGISTRY
from ds_vis.core.scene.scene_graph import SceneGraph


def test_schema_registry_validates_unknown_kind():
    scene_graph = SceneGraph()
    cmd = Command("s1", CommandType.CREATE_STRUCTURE, payload={"kind": "unknown"})
    with pytest.raises(CommandError, match="Unsupported command/kind"):
        scene_graph.apply_command(cmd)


def test_schema_registry_validates_missing_field():
    scene_graph = SceneGraph()
    cmd = Command("s1", CommandType.DELETE_NODE, payload={"kind": "list"})
    with pytest.raises(CommandError, match="Missing required field: index"):
        scene_graph.apply_command(cmd)


def test_model_op_registry_is_configured():
    assert MODEL_OP_REGISTRY[(CommandType.CREATE_STRUCTURE, "list")] == "create"
    assert MODEL_OP_REGISTRY[(CommandType.DELETE_STRUCTURE, "list")] == "delete_all"
    assert MODEL_OP_REGISTRY[(CommandType.SEARCH, "list")] == "search"
    assert MODEL_OP_REGISTRY[(CommandType.UPDATE, "list")] == "update"
    assert MODEL_OP_REGISTRY[(CommandType.CREATE_STRUCTURE, "stack")] == "create"
    assert MODEL_OP_REGISTRY[(CommandType.INSERT, "stack")] == "push"
    assert MODEL_OP_REGISTRY[(CommandType.DELETE_NODE, "stack")] == "pop"
    assert MODEL_OP_REGISTRY[(CommandType.SEARCH, "stack")] == "search"
    assert MODEL_OP_REGISTRY[(CommandType.CREATE_STRUCTURE, "bst")] == "create"
    assert MODEL_OP_REGISTRY[(CommandType.INSERT, "bst")] == "insert"
    assert MODEL_OP_REGISTRY[(CommandType.CREATE_STRUCTURE, "huffman")] == "build"
    assert MODEL_OP_REGISTRY[(CommandType.CREATE_STRUCTURE, "git")] == "init"
    assert MODEL_OP_REGISTRY[(CommandType.INSERT, "git")] == "commit"
    assert MODEL_OP_REGISTRY[(CommandType.SEARCH, "git")] == "checkout"


def test_schema_registry_rejects_extra_fields():
    scene_graph = SceneGraph()
    cmd = Command(
        "s1",
        CommandType.CREATE_STRUCTURE,
        payload={"kind": "list", "values": [1], "extra": True},
    )
    with pytest.raises(CommandError, match="Unexpected payload fields"):
        scene_graph.apply_command(cmd)
