import pytest

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.list_model import ListModel
from ds_vis.core.ops import OpCode


def _ops(op_code, timeline):
    return [
        op
        for step in timeline.steps
        for op in step.ops
        if op.op is op_code
    ]


def test_insert_at_head_rewires_edges_and_keeps_ids():
    model = ListModel(structure_id="lst")
    model.create([2, 3])

    timeline = model.insert(index=0, value=1)

    assert model.values == [1, 2, 3]
    edge_targets = [op.target for op in _ops(OpCode.CREATE_EDGE, timeline)]
    assert edge_targets == ["lst|next|lst_node_2->lst_node_0"]
    # Original nodes keep IDs; new node is monotonic (node_2)
    assert model._node_ids == ["lst_node_2", "lst_node_0", "lst_node_1"]


def test_insert_at_tail_appends_and_links():
    model = ListModel(structure_id="lst")
    model.create([1, 2])

    timeline = model.insert(index=2, value=3)

    assert model.values == [1, 2, 3]
    edge_targets = [op.target for op in _ops(OpCode.CREATE_EDGE, timeline)]
    assert edge_targets == ["lst|next|lst_node_1->lst_node_2"]
    assert model._node_ids[-1] == "lst_node_2"


def test_insert_into_empty_list_creates_first_node():
    model = ListModel(structure_id="lst")

    timeline = model.insert(index=0, value=42)

    node_targets = [op.target for op in _ops(OpCode.CREATE_NODE, timeline)]
    assert node_targets == ["lst_node_0"]
    assert model.values == [42]
    assert model.node_count == 1


def test_insert_out_of_range_raises():
    model = ListModel(structure_id="lst")
    model.create([1])

    with pytest.raises(ModelError):
        model.insert(index=-1, value=0)
    with pytest.raises(ModelError):
        model.insert(index=3, value=0)
