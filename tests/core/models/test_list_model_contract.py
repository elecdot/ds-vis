import pytest

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.list_model import ListModel
from ds_vis.core.ops import OpCode


def _collect_ops(timeline, op_code):
    return [
        op
        for step in timeline.steps
        for op in step.ops
        if op.op is op_code
    ]


def test_list_model_uses_monotonic_ids_and_edge_keys():
    model = ListModel(structure_id="lst")

    first = model.create([1, 2])
    node_ids_first = [op.target for op in _collect_ops(first, OpCode.CREATE_NODE)]
    edge_ids_first = [op.target for op in _collect_ops(first, OpCode.CREATE_EDGE)]

    assert node_ids_first == ["lst_node_0", "lst_node_1"]
    assert edge_ids_first == ["lst|next|lst_node_0->lst_node_1"]

    recreated = model.recreate([9])
    node_ids_second = [op.target for op in _collect_ops(recreated, OpCode.CREATE_NODE)]

    assert node_ids_second == ["lst_node_2"]  # monotonic, not reset on recreate


def test_list_model_node_count_tracks_state():
    model = ListModel(structure_id="lst")
    assert model.node_count == 0

    model.create([1])
    assert model.node_count == 1

    model.delete_all()
    assert model.node_count == 0


def test_delete_index_out_of_range_raises_model_error():
    model = ListModel(structure_id="lst")
    model.create([1, 2])

    with pytest.raises(ModelError, match="out of range"):
        model.delete_index(5)
