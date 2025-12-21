from ds_vis.core.models.list_model import ListModel
from ds_vis.core.ops import OpCode


def _collect_ops(timeline, op_code):
    return [
        op
        for step in timeline.steps
        for op in step.ops
        if op.op is op_code
    ]


def test_create_empty_list_emits_sentinel_but_keeps_node_count_zero():
    model = ListModel(structure_id="lst")
    timeline = model.create([])

    assert model.node_count == 0
    create_ops = _collect_ops(timeline, OpCode.CREATE_NODE)
    assert create_ops
    assert any(op.data.get("kind") == "list_sentinel" for op in create_ops)
