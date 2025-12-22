import pytest

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.seqlist import SeqlistModel
from ds_vis.core.ops import OpCode


def _ops_by_code(timeline, code: OpCode):
    return [
        op for step in timeline.steps for op in step.ops if op.op is code
    ]


def test_create_and_insert_generates_nodes():
    model = SeqlistModel(structure_id="seq1")
    tl = model.create(values=[1, 2])
    creates = _ops_by_code(tl, OpCode.CREATE_NODE)
    # bucket + two cells
    assert len(creates) == 3

    ins = model.insert(1, 3)
    creates_ins = _ops_by_code(ins, OpCode.CREATE_NODE)
    # new node + resized bucket
    assert len(creates_ins) == 2
    assert model.values == [1, 3, 2]


def test_insert_out_of_range_raises():
    model = SeqlistModel(structure_id="seq_err")
    with pytest.raises(ModelError):
        model.insert(1, 5)


def test_delete_index_updates_state():
    model = SeqlistModel(structure_id="seq_del")
    model.create([1, 2, 3])
    tl = model.delete_index(1)
    deletes = _ops_by_code(tl, OpCode.DELETE_NODE)
    # delete node + resized bucket
    assert len(deletes) == 2
    assert model.values == [1, 3]


def test_search_hit_and_miss():
    model = SeqlistModel(structure_id="seq_search")
    model.create([4, 5])

    hit = model.search(value=5)
    assert any(
        op.op is OpCode.SET_MESSAGE and "Found" in op.data.get("text", "")
        for step in hit.steps
        for op in step.ops
    )

    miss = model.search(value=9)
    assert any(
        op.op is OpCode.SET_MESSAGE and "Not found" in op.data.get("text", "")
        for step in miss.steps
        for op in step.ops
    )


def test_update_by_index_and_value():
    model = SeqlistModel(structure_id="seq_update")
    model.create([1, 2, 3])
    tl_idx = model.update(new_value=9, index=1)
    set_labels = _ops_by_code(tl_idx, OpCode.SET_LABEL)
    assert any(op.data.get("label") == "9" for op in set_labels)
    model.update(new_value=7, value=3)
    assert model.values == [1, 9, 7]
