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


def test_search_by_value_emits_message_and_traversal():
    model = ListModel(structure_id="lst")
    model.create([1, 2, 3])

    timeline = model.search(value=2)
    assert model.values == [1, 2, 3]

    message_ops = _collect_ops(timeline, OpCode.SET_MESSAGE)
    assert message_ops
    assert any("found" in str(op.data.get("text", "")).lower() for op in message_ops)

    state_ops = _collect_ops(timeline, OpCode.SET_STATE)
    assert any(op.data.get("state") == "highlight" for op in state_ops)
    assert any(op.data.get("state") == "normal" for op in state_ops)


def test_search_by_index_emits_message():
    model = ListModel(structure_id="lst")
    model.create([10, 20, 30])

    timeline = model.search(index=1)
    message_ops = _collect_ops(timeline, OpCode.SET_MESSAGE)
    assert message_ops
    assert any("found" in str(op.data.get("text", "")).lower() for op in message_ops)


def test_search_rejects_missing_target():
    model = ListModel(structure_id="lst")
    model.create([1])

    with pytest.raises(ModelError):
        model.search()


def test_update_by_index_sets_label_and_updates_value():
    model = ListModel(structure_id="lst")
    model.create([1, 2, 3])

    timeline = model.update(index=1, new_value=9)
    assert model.values == [1, 9, 3]

    label_ops = _collect_ops(timeline, OpCode.SET_LABEL)
    assert any(
        op.target == "lst_node_1" and op.data.get("text") == "9"
        for op in label_ops
    )


def test_update_by_value_sets_label_and_updates_first_match():
    model = ListModel(structure_id="lst")
    model.create([4, 5, 6, 5])

    timeline = model.update(value=5, new_value=8)
    assert model.values == [4, 8, 6, 5]

    label_ops = _collect_ops(timeline, OpCode.SET_LABEL)
    assert any(op.data.get("text") == "8" for op in label_ops)


def test_update_rejects_missing_target():
    model = ListModel(structure_id="lst")
    model.create([1])

    with pytest.raises(ModelError):
        model.update(new_value=2)
