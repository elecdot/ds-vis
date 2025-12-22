from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.bst import BstModel
from ds_vis.core.ops import OpCode


def test_search_hit_and_miss():
    model = BstModel(structure_id="bst_search")
    model.create(values=[5, 3, 7])

    hit = model.search(7)
    miss = model.search(10)

    assert any(
        op.op is OpCode.SET_MESSAGE and "Found" in op.data.get("text", "")
        for step in hit.steps
        for op in step.ops
    )
    assert any(
        op.op is OpCode.SET_MESSAGE and "not found" in op.data.get("text", "").lower()
        for step in miss.steps
        for op in step.ops
    )


def test_delete_leaf_and_single_child():
    model = BstModel(structure_id="bst_delete")
    model.create(values=[5, 3, 7])

    leaf_tl = model.delete_value(3)
    # after deleting leaf, node count should reduce
    assert model.node_count == 2
    assert any(
        op.op is OpCode.DELETE_NODE for step in leaf_tl.steps for op in step.ops
    )

    # delete node with single child (insert left-heavy)
    model.insert(2)
    model.insert(1)
    single_child_tl = model.delete_value(2)
    assert any(
        op.op is OpCode.DELETE_NODE
        for step in single_child_tl.steps
        for op in step.ops
    )


def test_delete_two_children_uses_successor_label():
    model = BstModel(structure_id="bst_delete_successor")
    model.create(values=[5, 3, 7, 6])
    tl = model.delete_value(5)
    # Should update root label to successor (6)
    label_ops = [
        op
        for step in tl.steps
        for op in step.ops
        if op.op is OpCode.SET_LABEL
    ]
    assert any("6" in str(op.data.get("label")) for op in label_ops)


def test_delete_two_children_successor_with_child_rewires_edges():
    model = BstModel(structure_id="bst_delete_successor_child")
    model.create(values=[5, 3, 7, 8])

    model.delete_value(5)

    # root should keep id but adopt successor key
    root_id = model._root_id
    assert root_id is not None
    root = model._nodes[root_id]
    assert root.key == 7

    child_8 = next(nid for nid, node in model._nodes.items() if node.key == 8)
    assert root.right == child_8
    assert model._nodes[child_8].parent == root_id


def test_delete_value_requires_value():
    model = BstModel(structure_id="bst_delete2")
    try:
        model.delete_value(None)
    except ModelError:
        pass
    else:
        raise AssertionError("delete_value without value should raise")
