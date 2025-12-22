from ds_vis.core.layout.tree import TreeLayoutEngine
from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline


def _pos_map(timeline: Timeline):
    return {
        op.target: (op.data.get("x"), op.data.get("y"))
        for step in timeline.steps
        for op in step.ops
        if op.op is OpCode.SET_POS
    }


def test_huffman_queue_and_tree_offsets():
    engine = TreeLayoutEngine()
    engine.set_offsets({"h1": (0.0, 0.0)})
    engine.set_structure_config(
        {
            "h1": {
                "queue_spacing": 60.0,
                "queue_start_y": 10.0,
                "tree_offset_y": 100.0,
                "tree_span": 120.0,
            }
        }
    )
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="a",
                        data={"structure_id": "h1", "queue_index": 0},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="b",
                        data={"structure_id": "h1", "queue_index": 1},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="parent",
                        data={"structure_id": "h1", "queue_index": 2},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_EDGE,
                        target="e1",
                        data={
                            "structure_id": "h1",
                            "from": "parent",
                            "to": "a",
                            "label": "L",
                        },
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_EDGE,
                        target="e2",
                        data={
                            "structure_id": "h1",
                            "from": "parent",
                            "to": "b",
                            "label": "R",
                        },
                    ),
                ]
            )
        ]
    )
    laid_out = engine.apply_layout(timeline)
    pos = _pos_map(laid_out)
    assert pos["parent"][0] == engine.start_x
    assert pos["parent"][1] == 10.0
    # children 放在 tree_offset_y 之下，并左右分离
    assert pos["a"][1] == 110.0
    assert pos["b"][1] == 110.0
    assert pos["a"][0] < pos["parent"][0] < pos["b"][0]
