import pytest

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.command_schema import MODEL_OP_REGISTRY, SCHEMA_REGISTRY


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

    with pytest.raises(CommandError, match="Field 'values' must be a list or tuple"):
        scene_graph.apply_command(cmd)


def test_create_structure_requires_kind(scene_graph):
    cmd = Command("list_schema", CommandType.CREATE_STRUCTURE, payload={})

    with pytest.raises(CommandError, match="requires payload.kind"):
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

    with pytest.raises(CommandError, match="Field 'index' must be int"):
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


def test_delete_node_requires_index_for_list(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1]
        )
    )
    cmd = Command("list_schema", CommandType.DELETE_NODE, payload={"kind": "list"})

    with pytest.raises(CommandError, match="Missing required field"):
        scene_graph.apply_command(cmd)


def test_delete_node_accepts_empty_payload_for_other_structures(scene_graph):
    cmd = Command("tree_1", CommandType.DELETE_NODE, payload={})
    # For unknown kinds, payload validation should not block future schemas; handler
    # will error later.
    with pytest.raises(CommandError):
        scene_graph.apply_command(cmd)


def test_schema_registry_contains_known_mappings():
    assert SCHEMA_REGISTRY[(CommandType.CREATE_STRUCTURE, "list")]
    assert MODEL_OP_REGISTRY[(CommandType.DELETE_NODE, "list")] == "delete_index"


def test_insert_requires_index_and_value(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1]
        )
    )
    missing = Command("list_schema", CommandType.INSERT, payload={"kind": "list"})
    with pytest.raises(CommandError, match="Missing required field: index"):
        scene_graph.apply_command(missing)

    wrong_index = Command(
        "list_schema",
        CommandType.INSERT,
        payload={"kind": "list", "index": "1", "value": 2},
    )
    with pytest.raises(CommandError, match="Field 'index' must be int"):
        scene_graph.apply_command(wrong_index)


def test_model_op_registry_includes_insert():
    assert MODEL_OP_REGISTRY[(CommandType.INSERT, "list")] == "insert"


def test_insert_requires_value(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1]
        )
    )
    missing_value = Command(
        "list_schema",
        CommandType.INSERT,
        payload={"kind": "list", "index": 0},
    )
    with pytest.raises(CommandError, match="Missing required field: value"):
        scene_graph.apply_command(missing_value)


def test_search_requires_index_or_value(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1]
        )
    )
    missing = Command("list_schema", CommandType.SEARCH, payload={"kind": "list"})
    with pytest.raises(CommandError, match="requires index or value"):
        scene_graph.apply_command(missing)


def test_update_requires_new_value_and_target(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_schema", CommandType.CREATE_STRUCTURE, kind="list", values=[1]
        )
    )
    missing_target = Command(
        "list_schema", CommandType.UPDATE, payload={"kind": "list", "new_value": 2}
    )
    with pytest.raises(CommandError, match="requires index or value"):
        scene_graph.apply_command(missing_target)

    missing_new = Command(
        "list_schema",
        CommandType.UPDATE,
        payload={"kind": "list", "index": 0},
    )
    with pytest.raises(CommandError, match="Missing required field: new_value"):
        scene_graph.apply_command(missing_new)


def test_model_op_registry_includes_search_and_update():
    assert MODEL_OP_REGISTRY[(CommandType.SEARCH, "list")] == "search"
    assert MODEL_OP_REGISTRY[(CommandType.UPDATE, "list")] == "update"
