import pytest

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.stack import StackModel
from ds_vis.core.ops import OpCode


def _ops_by_code(timeline, code: OpCode):
    return [
        op for step in timeline.steps for op in step.ops if op.op is code
    ]


def test_create_push_pop_updates_nodes_and_values():
    model = StackModel(structure_id="stack1")
    tl_create = model.create(values=[1, 2])
    creates = _ops_by_code(tl_create, OpCode.CREATE_NODE)
    # bucket + 2 cells
    assert len(creates) == 3
    # index 注入确保 top 在 index=0
    cell_indexes = [
        op.data.get("index") for op in creates if op.data.get("shape") != "bucket"
    ]
    assert cell_indexes == [0, 1]
    # 输入按 push 顺序解释，2 在栈顶（index 0）
    assert model.values[0] == 2

    tl_push = model.push(3)
    creates_push = _ops_by_code(tl_push, OpCode.CREATE_NODE)
    # 新节点 + 重建桶
    assert len(creates_push) == 2
    assert any(op.data.get("index") == 0 for op in creates_push if op.target)
    assert model.values[0] == 3

    tl_pop = model.pop()
    deletes = _ops_by_code(tl_pop, OpCode.DELETE_NODE)
    # 删除栈顶 + 重建桶
    assert len(deletes) == 2
    assert model.values[0] == 2


def test_push_pop_validations_and_empty_pop():
    model = StackModel(structure_id="stack_err")
    with pytest.raises(ModelError):
        model.push(None)
    with pytest.raises(ModelError):
        model.push(1, index=1)
    with pytest.raises(ModelError):
        model.pop(index=2)

    tl = model.pop()
    assert any(op.op is OpCode.SET_MESSAGE for step in tl.steps for op in step.ops)


def test_stack_search_hit_and_miss():
    model = StackModel(structure_id="stack_search")
    model.create(values=[1, 2])

    hit = model.search(value=2)
    assert any(
        op.op is OpCode.SET_MESSAGE and "Found" in op.data.get("text", "")
        for step in hit.steps
        for op in step.ops
    )

    miss = model.search(value=99)
    assert any(
        op.op is OpCode.SET_MESSAGE and "Not found" in op.data.get("text", "")
        for step in miss.steps
        for op in step.ops
    )
