from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.bst import BstModel
from ds_vis.core.ops import OpCode


def test_create_root_and_values():
    model = BstModel(structure_id="tree1")
    tl = model.create(values=[2, 1, 3])

    assert model.node_count == 3
    # ensure ops include root creation
    create_ops = [
        op for step in tl.steps for op in step.ops if op.op is OpCode.CREATE_NODE
    ]
    assert len(create_ops) == 3


def test_insert_left_and_right():
    model = BstModel(structure_id="tree2")
    model.create(values=[5])

    left_tl = model.insert(3)
    right_tl = model.insert(7)

    # after two inserts, we should have 3 nodes and two edges
    assert model.node_count == 3
    # check last insert timeline contains edge with label L/R
    left_edges = [
        op
        for step in left_tl.steps
        for op in step.ops
        if op.op is OpCode.CREATE_EDGE
    ]
    right_edges = [
        op
        for step in right_tl.steps
        for op in step.ops
        if op.op is OpCode.CREATE_EDGE
    ]
    assert left_edges and right_edges
    assert left_edges[0].data.get("label") == "L"
    assert right_edges[0].data.get("label") == "R"


def test_insert_requires_value():
    model = BstModel(structure_id="tree3")
    try:
        model.insert(None)
    except ModelError:
        pass
    else:
        raise AssertionError("insert without value should raise")
