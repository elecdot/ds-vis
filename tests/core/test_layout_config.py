from ds_vis.core.layout.simple import SimpleLayoutEngine
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline
from ds_vis.core.scene.scene_graph import SceneGraph


def test_simple_layout_vertical_orientation_positions():
    """Vertical orientation should stack nodes along y while keeping x constant."""
    engine = SimpleLayoutEngine(spacing=80.0, row_spacing=200.0)
    engine.set_offsets({"stack_1": (0.0, 0.0)})
    engine.set_structure_config(
        {
            "stack_1": {
                "orientation": "vertical",
                "spacing": 50.0,
                "start_x": 10.0,
                "start_y": 20.0,
            }
        }
    )

    timeline = Timeline()
    step = AnimationStep(
        ops=[
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target="n1",
                data={"structure_id": "stack_1"},
            ),
            AnimationOp(
                op=OpCode.CREATE_NODE,
                target="n2",
                data={"structure_id": "stack_1"},
            ),
        ]
    )
    timeline.add_step(step)

    laid_out = engine.apply_layout(timeline)
    pos_ops = [op for op in laid_out.steps[0].ops if op.op is OpCode.SET_POS]
    assert len(pos_ops) == 2
    x_positions = {op.target: op.data["x"] for op in pos_ops}
    y_positions = {op.target: op.data["y"] for op in pos_ops}
    assert x_positions["n1"] == x_positions["n2"] == 10.0
    assert y_positions["n2"] - y_positions["n1"] == 50.0


def test_scene_graph_offsets_and_layout_config_by_kind():
    """SceneGraph should assign offsets and layout config per kind map."""
    sg = SceneGraph()
    sg._assign_offset("list_1", "seqlist")
    sg._assign_layout_config("list_1", "seqlist")
    sg._assign_offset("stack_1", "stack")
    sg._assign_layout_config("stack_1", "stack")
    sg._assign_offset("git_1", "git")
    sg._assign_layout_config("git_1", "git")

    # list/seqlist should start at origin row 0
    assert sg._structure_offsets["list_1"] == (0.0, 0.0)
    # stack uses LINEAR strategy row 1 by now -> y offset > 0
    assert sg._structure_offsets["stack_1"][1] > 0.0
    # git uses DAG strategy with horizontal lane offset
    assert sg._structure_offsets["git_1"][0] >= 200.0

    # layout config reflects orientation defaults
    assert sg._structure_layout_config["stack_1"]["orientation"] == "vertical"
    assert sg._structure_layout_config["list_1"]["orientation"] == "horizontal"
    assert sg._structure_layout_config["git_1"]["orientation"] == "vertical"
