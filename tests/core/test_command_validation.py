import pytest

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command, CommandType


def test_payload_must_be_mapping(scene_graph):
    cmd = Command("list_schema", CommandType.CREATE_STRUCTURE, payload="oops")

    with pytest.raises(CommandError, match="payload must be a mapping"):
        scene_graph.apply_command(cmd)


def test_create_structure_rejects_unknown_fields(scene_graph):
    cmd = Command(
        "list_schema",
        CommandType.CREATE_STRUCTURE,
        payload={"kind": "list", "values": [1], "unexpected": True},
    )

    with pytest.raises(CommandError, match="Unexpected payload fields"):
        scene_graph.apply_command(cmd)


def test_create_structure_values_must_be_sequence(scene_graph):
    cmd = Command(
        "list_schema",
        CommandType.CREATE_STRUCTURE,
        payload={"kind": "list", "values": "abc"},
    )

    with pytest.raises(CommandError, match="values must be a list or tuple"):
        scene_graph.apply_command(cmd)


def test_delete_node_requires_int_index(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2]
        )
    )
    cmd = Command(
        "list_schema",
        CommandType.DELETE_NODE,
        payload={"kind": "list", "index": "1"},
    )

    with pytest.raises(CommandError, match="index must be int"):
        scene_graph.apply_command(cmd)


def test_delete_node_rejects_unknown_fields(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2]
        )
    )
    cmd = Command(
        "list_schema",
        CommandType.DELETE_NODE,
        payload={"kind": "list", "index": 0, "extra": 123},
    )

    with pytest.raises(CommandError, match="Unexpected payload fields"):
        scene_graph.apply_command(cmd)
