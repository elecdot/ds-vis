"""
SceneGraph + layout integration tests (tracer bullets).
"""

from ds_vis.core.exceptions import CommandError
from ds_vis.core.ops import OpCode
from ds_vis.core.scene.command import Command, CommandType


def test_scene_graph_returns_timeline(scene_graph, create_cmd_factory):
    cmd = create_cmd_factory("test_list", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)

    assert timeline is not None
    assert hasattr(timeline, "steps")

def test_create_structure_produces_ops(scene_graph, create_cmd_factory):
    cmd = create_cmd_factory("list_1", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)

    assert len(timeline.steps) > 0
    ops = timeline.steps[0].ops
    assert any(op.op == OpCode.CREATE_NODE for op in ops)


def test_layout_injects_positions(scene_graph, create_cmd_factory):
    cmd = create_cmd_factory("list_2", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)

    all_ops = [op for step in timeline.steps for op in step.ops]
    assert any(op.op == OpCode.SET_POS for op in all_ops)


def test_list_ids_monotonic_and_layout_refresh(scene_graph, create_cmd_factory):
    """
    IDs should be monotonic per structure; layout refreshes after delete/recreate.
    """
    create_cmd = create_cmd_factory(
        "list_ids", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2]
    )
    timeline1 = scene_graph.apply_command(create_cmd)
    node_ids_first = [
        op.target
        for step in timeline1.steps
        for op in step.ops
        if op.op == OpCode.CREATE_NODE
    ]
    assert node_ids_first == ["list_ids_node_0", "list_ids_node_1"]

    delete_cmd = create_cmd_factory(
        "list_ids", CommandType.DELETE_STRUCTURE, kind="list"
    )
    timeline2 = scene_graph.apply_command(delete_cmd)
    delete_ops = [
        op for step in timeline2.steps for op in step.ops if op.op == OpCode.DELETE_NODE
    ]
    assert len(delete_ops) == 2

    recreate_cmd = create_cmd_factory(
        "list_ids", CommandType.CREATE_STRUCTURE, kind="list", values=[9]
    )
    timeline3 = scene_graph.apply_command(recreate_cmd)
    node_ids_second = [
        op.target
        for step in timeline3.steps
        for op in step.ops
        if op.op == OpCode.CREATE_NODE
    ]
    assert node_ids_second == ["list_ids_node_2"]
    assert set(node_ids_first).isdisjoint(node_ids_second)

    set_pos_ops = [
        op for step in timeline3.steps for op in step.ops if op.op == OpCode.SET_POS
    ]
    assert set_pos_ops
    for op in set_pos_ops:
        assert op.data.get("x") == 50.0
        assert op.data.get("y") == 50.0


def test_unknown_command_raises_command_error(scene_graph):
    cmd = Command(structure_id="s1", type=CommandType.SEARCH, payload={})
    try:
        scene_graph.apply_command(cmd)
    except CommandError:
        pass
    else:  # pragma: no cover - safety
        raise AssertionError("Expected CommandError for unsupported command")


def test_list_delete_index_rewires_and_keeps_ids_monotonic(
    scene_graph, create_cmd_factory
):
    """
    Deleting a middle node removes adjacent edges and rewires neighbors with stable IDs.
    """
    create_cmd = create_cmd_factory(
        "list_delete", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2, 3]
    )
    timeline1 = scene_graph.apply_command(create_cmd)
    node_ids_first = [
        op.target
        for step in timeline1.steps
        for op in step.ops
        if op.op == OpCode.CREATE_NODE
    ]
    assert node_ids_first == [
        "list_delete_node_0",
        "list_delete_node_1",
        "list_delete_node_2",
    ]

    delete_cmd = create_cmd_factory(
        "list_delete", CommandType.DELETE_NODE, kind="list", index=1
    )
    timeline2 = scene_graph.apply_command(delete_cmd)
    ops2 = [op for step in timeline2.steps for op in step.ops]
    assert any(
        op.op == OpCode.DELETE_NODE and op.target == "list_delete_node_1"
        for op in ops2
    )
    assert any(
        op.op == OpCode.CREATE_EDGE
        and op.target
        == "list_delete|next|list_delete_node_0->list_delete_node_2"
        for op in ops2
    )

    set_pos_ops = [
        op for step in timeline2.steps for op in step.ops if op.op == OpCode.SET_POS
    ]
    assert set_pos_ops
    xs = sorted(op.data.get("x") for op in set_pos_ops)
    assert xs[0] == 50.0
    if len(xs) > 1:
        assert xs[1] - xs[0] == 120.0


def test_insert_routes_through_scene_graph_and_layout(scene_graph, create_cmd_factory):
    create_cmd = create_cmd_factory(
        "list_insert", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 3]
    )
    scene_graph.apply_command(create_cmd)

    insert_cmd = Command(
        "list_insert",
        CommandType.INSERT,
        payload={"kind": "list", "index": 1, "value": 2},
    )
    timeline = scene_graph.apply_command(insert_cmd)

    assert len(timeline.steps) >= 5

    highlight_step = next(
        (step for step in timeline.steps if step.label == "Highlight neighbors"),
        None,
    )
    assert highlight_step is not None
    step_state_ops = [
        op for op in highlight_step.ops if op.op is OpCode.SET_STATE
    ]
    assert {op.target for op in step_state_ops} == {
        "list_insert_node_0",
        "list_insert_node_1",
    }

    pos_step = next(
        (
            step
            for step in timeline.steps
            if any(op.op is OpCode.SET_POS for op in step.ops)
        ),
        None,
    )
    assert pos_step is not None
    step_positions = {
        op.target: (op.data.get("x"), op.data.get("y"))
        for op in pos_step.ops
        if op.op is OpCode.SET_POS
    }
    # New node inserted in the middle should shift the original second node.
    assert step_positions["list_insert_node_0"][0] == 50.0
    assert step_positions["list_insert_node_2"][0] == 50.0 + 120.0
    assert step_positions["list_insert_node_1"][0] == 50.0 + 120.0 * 2


def test_huffman_build_routes_and_positions(scene_graph, create_cmd_factory):
    cmd = create_cmd_factory(
        "huff_sg",
        CommandType.CREATE_STRUCTURE,
        kind="huffman",
        values=[1, 2, 3],
    )
    timeline = scene_graph.apply_command(cmd)
    all_ops = [op for step in timeline.steps for op in step.ops]
    assert any(op.op is OpCode.CREATE_NODE for op in all_ops)
    assert any(op.op is OpCode.SET_POS for op in all_ops)


def test_search_routes_and_emits_message(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_search", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2]
        )
    )
    search_cmd = Command(
        "list_search",
        CommandType.SEARCH,
        payload={"kind": "list", "index": 1},
    )
    timeline = scene_graph.apply_command(search_cmd)
    all_ops = [op for step in timeline.steps for op in step.ops]
    assert any(op.op is OpCode.SET_MESSAGE for op in all_ops)
    assert any(op.op is OpCode.SET_STATE for op in all_ops)


def test_update_routes_and_sets_label(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory(
            "list_update", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2]
        )
    )
    update_cmd = Command(
        "list_update",
        CommandType.UPDATE,
        payload={"kind": "list", "index": 1, "new_value": 9},
    )
    timeline = scene_graph.apply_command(update_cmd)
    all_ops = [op for step in timeline.steps for op in step.ops]
    assert any(op.op is OpCode.SET_LABEL for op in all_ops)
    assert any(op.op is OpCode.SET_STATE for op in all_ops)


def test_tree_create_and_insert_flow(scene_graph, create_cmd_factory):
    create_cmd = create_cmd_factory(
        "tree_1", CommandType.CREATE_STRUCTURE, kind="bst", values=[5]
    )
    timeline_create = scene_graph.apply_command(create_cmd)

    create_nodes = [
        op
        for step in timeline_create.steps
        for op in step.ops
        if op.op is OpCode.CREATE_NODE
    ]
    assert create_nodes
    assert any(
        op.op is OpCode.SET_POS for step in timeline_create.steps for op in step.ops
    )

    insert_cmd = create_cmd_factory(
        "tree_1", CommandType.INSERT, kind="bst", value=3
    )
    timeline_insert = scene_graph.apply_command(insert_cmd)

    edge_ops = [
        op
        for step in timeline_insert.steps
        for op in step.ops
        if op.op is OpCode.CREATE_EDGE
    ]
    assert edge_ops
    assert edge_ops[0].data.get("label") in ("L", "R")
