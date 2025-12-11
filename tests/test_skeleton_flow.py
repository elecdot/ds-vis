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
