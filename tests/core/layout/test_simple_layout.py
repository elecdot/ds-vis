from ds_vis.core.layout.simple import SimpleLayoutEngine
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


def _set_pos_targets(timeline: Timeline):
    return {
        op.target: (op.data.get("x"), op.data.get("y"))
        for step in timeline.steps
        for op in step.ops
        if op.op is OpCode.SET_POS
    }


def test_multi_structure_vertical_spacing():
    layout = SimpleLayoutEngine()

    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="a1",
                        data={"structure_id": "a"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="b1",
                        data={"structure_id": "b"},
                    ),
                ]
            )
        ]
    )

    laid_out = layout.apply_layout(timeline)
    pos = _set_pos_targets(laid_out)

    assert pos["a1"] == (layout.start_x, layout.start_y)
    assert pos["b1"] == (layout.start_x, layout.start_y + layout.row_spacing)


def test_dirty_check_skips_unchanged_nodes():
    layout = SimpleLayoutEngine()
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s"},
                    ),
                ]
            ),
            AnimationStep(
                ops=[]
            ),  # no structural change; should not emit additional SET_POS
        ]
    )

    laid_out = layout.apply_layout(timeline)
    set_pos_counts = [
        len([op for op in step.ops if op.op is OpCode.SET_POS])
        for step in laid_out.steps
    ]

    assert set_pos_counts[0] == 2
    assert set_pos_counts[1] == 0


def test_delete_repositions_remaining_nodes():
    layout = SimpleLayoutEngine()
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s"},
                    ),
                ]
            ),
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.DELETE_NODE,
                        target="n1",
                        data={"structure_id": "s"},
                    )
                ]
            ),
        ]
    )

    laid_out = layout.apply_layout(timeline)
    step1_pos = {
        op.target: (op.data.get("x"), op.data.get("y"))
        for op in laid_out.steps[0].ops
        if op.op is OpCode.SET_POS
    }
    step2_pos = {
        op.target: (op.data.get("x"), op.data.get("y"))
        for op in laid_out.steps[1].ops
        if op.op is OpCode.SET_POS
    }

    assert step1_pos["n1"] == (layout.start_x, layout.start_y)
    assert step1_pos["n2"] == (layout.start_x + layout.spacing, layout.start_y)
    # After deleting n1, n2 shifts to the first slot and should be marked dirty.
    assert step2_pos["n2"] == (layout.start_x, layout.start_y)


def test_create_node_with_index_inserts_order():
    layout = SimpleLayoutEngine()
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n0",
                        data={"structure_id": "s"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s"},
                    ),
                ]
            ),
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s", "index": 1},
                    ),
                ]
            ),
        ]
    )

    laid_out = layout.apply_layout(timeline)
    step2_pos = {
        op.target: (op.data.get("x"), op.data.get("y"))
        for op in laid_out.steps[1].ops
        if op.op is OpCode.SET_POS
    }

    assert step2_pos["n0"] == (layout.start_x, layout.start_y)
    assert step2_pos["n2"] == (layout.start_x + layout.spacing, layout.start_y)
    assert step2_pos["n1"] == (layout.start_x + 2 * layout.spacing, layout.start_y)


def test_head_insert_shifts_all_nodes_right():
    layout = SimpleLayoutEngine()
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s"},
                    ),
                ]
            ),
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n0",
                        data={"structure_id": "s", "index": 0},
                    )
                ]
            ),
        ]
    )

    laid_out = layout.apply_layout(timeline)
    step2_pos = {
        op.target: (op.data.get("x"), op.data.get("y"))
        for op in laid_out.steps[1].ops
        if op.op is OpCode.SET_POS
    }

    assert step2_pos["n0"] == (layout.start_x, layout.start_y)
    assert step2_pos["n1"] == (layout.start_x + layout.spacing, layout.start_y)
    assert step2_pos["n2"] == (layout.start_x + 2 * layout.spacing, layout.start_y)


def test_reset_clears_state_for_rebuild():
    layout = SimpleLayoutEngine()
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s"},
                    ),
                ]
            )
        ]
    )
    laid_out1 = layout.apply_layout(timeline)
    pos1 = _set_pos_targets(laid_out1)
    assert pos1["n1"] == (layout.start_x, layout.start_y)

    layout.reset()
    assert layout._structure_nodes == {}

    laid_out2 = layout.apply_layout(timeline)
    pos2 = _set_pos_targets(laid_out2)
    assert pos2["n1"] == (layout.start_x, layout.start_y)
