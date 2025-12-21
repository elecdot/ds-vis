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


def test_apply_operation_routes_and_validates():
    model = ListModel(structure_id="lst")
    model.apply_operation("create", {"values": [1]})
    assert model.node_count == 1

    with pytest.raises(ModelError):
        model.apply_operation("delete_index", {"index": "bad"})

    with pytest.raises(ModelError):
        model.apply_operation("unknown", {})


def test_custom_id_allocator_can_override_default():
    def custom_allocator(structure_id: str, prefix: str, counter: int) -> str:
        return f"{structure_id}-{prefix}-custom-{counter}"

    model = ListModel(structure_id="lst", id_allocator=custom_allocator)
    timeline = model.create([1])
    node_ids = [op.target for op in _collect_ops(timeline, OpCode.CREATE_NODE)]

    assert node_ids == ["lst-node-custom-0"]


def test_insert_emits_microsteps_and_rewires():
    model = ListModel(structure_id="lst")
    model.create([1, 3])

    timeline = model.insert(index=1, value=2)
    labels = [step.label for step in timeline.steps]

    assert model.values == [1, 2, 3]

    traverse_steps = [step for step in timeline.steps if step.label == "Traverse node"]
    assert traverse_steps
    assert any(
        op.op is OpCode.SET_STATE
        and op.target == "lst_node_0"
        and op.data.get("state") == "highlight"
        for step in traverse_steps
        for op in step.ops
    )
    reset_steps = [step for step in timeline.steps if step.label == "Traverse reset"]
    assert any(
        op.op is OpCode.SET_STATE
        and op.target == "lst_node_0"
        and op.data.get("state") == "normal"
        for step in reset_steps
        for op in step.ops
    )

    highlight_step = timeline.steps[labels.index("Highlight neighbors")]
    highlight_ops = [op for op in highlight_step.ops if op.op is OpCode.SET_STATE]
    assert {op.target for op in highlight_ops} == {"lst_node_0", "lst_node_1"}
    assert all(op.data.get("state") == "highlight" for op in highlight_ops)

    highlight_link_step = timeline.steps[labels.index("Highlight link")]
    assert any(
        op.op is OpCode.SET_STATE
        and op.target == "lst|next|lst_node_0->lst_node_1"
        and op.data.get("state") == "highlight"
        for op in highlight_link_step.ops
    )

    delete_step = timeline.steps[labels.index("Remove old link")]
    assert any(
        op.op is OpCode.DELETE_EDGE
        and op.target == "lst|next|lst_node_0->lst_node_1"
        for op in delete_step.ops
    )

    create_step = timeline.steps[labels.index("Create new node")]
    assert any(
        op.op is OpCode.CREATE_NODE and op.target == "lst_node_2"
        for op in create_step.ops
    )
    assert any(
        op.op is OpCode.SET_STATE
        and op.target == "lst_node_2"
        and op.data.get("state") == "highlight"
        for op in create_step.ops
    )

    rewire_step = timeline.steps[labels.index("Rewire links")]
    assert any(
        op.op is OpCode.CREATE_EDGE
        and op.target == "lst|next|lst_node_0->lst_node_2"
        for op in rewire_step.ops
    )
    assert any(
        op.op is OpCode.CREATE_EDGE
        and op.target == "lst|next|lst_node_2->lst_node_1"
        for op in rewire_step.ops
    )
    assert any(
        op.op is OpCode.SET_STATE
        and op.target == "lst|next|lst_node_0->lst_node_2"
        and op.data.get("state") == "highlight"
        for op in rewire_step.ops
    )
    assert any(
        op.op is OpCode.SET_STATE
        and op.target == "lst|next|lst_node_2->lst_node_1"
        and op.data.get("state") == "highlight"
        for op in rewire_step.ops
    )

    restore_step = timeline.steps[labels.index("Restore state")]
    restore_ops = [op for op in restore_step.ops if op.op is OpCode.SET_STATE]
    assert {
        op.target for op in restore_ops
    } == {
        "lst_node_0",
        "lst_node_1",
        "lst_node_2",
        "lst|next|lst_node_0->lst_node_2",
        "lst|next|lst_node_2->lst_node_1",
    }
    assert all(op.data.get("state") == "normal" for op in restore_ops)
