from ds_vis.core.ops import OpCode
from ds_vis.core.scene.command import CommandType


def test_scene_graph_returns_timeline(scene_graph, create_cmd_factory):
    """
    Tracer Bullet Test:
    Verifies that sending a command to SceneGraph returns a Timeline object.
    This tests the basic plumbing of the architecture.
    """
    cmd = create_cmd_factory("test_list", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)
    
    # Basic plumbing check: we should get a Timeline object back
    assert timeline is not None
    # Ideally, it should have steps, but for now just checking type is enough to prove
    # the environment is working.
    assert hasattr(timeline, "steps")

def test_create_structure_produces_ops(scene_graph, create_cmd_factory):
    """
    Ensures creating a structure produces structural ops (CREATE_NODE).
    """
    cmd = create_cmd_factory("list_1", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)

    # We expect at least one step with CREATE_NODE op
    assert len(timeline.steps) > 0
    ops = timeline.steps[0].ops
    assert any(op.op == OpCode.CREATE_NODE for op in ops)


def test_layout_injects_positions(scene_graph, create_cmd_factory):
    """
    Layout engine should inject SET_POS ops alongside structural ops.
    """
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

    delete_cmd = create_cmd_factory("list_ids", CommandType.DELETE)
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
