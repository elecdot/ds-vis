from ds_vis.core.models.huffman import HuffmanModel
from ds_vis.core.ops import OpCode


def _ops_by_code(timeline, code: OpCode):
    return [
        op for step in timeline.steps for op in step.ops if op.op is code
    ]


def test_huffman_build_generates_parents_and_edges():
    model = HuffmanModel(structure_id="huff1")
    tl = model.build([3, 1, 2])
    creates = _ops_by_code(tl, OpCode.CREATE_NODE)
    edges = _ops_by_code(tl, OpCode.CREATE_EDGE)
    # 3 leaves + 2 parents
    assert len(creates) == 5
    assert len(edges) == 4
    # queue_index 应按初始排序
    init_indexes = [
        op.data.get("queue_index")
        for op in creates
        if op.data.get("queue_index") is not None
    ]
    assert sorted(init_indexes) == [0, 1, 2]
    assert model.node_count == 5


def test_huffman_delete_all_clears_nodes():
    model = HuffmanModel(structure_id="huff_del")
    model.build([1, 2])
    tl = model.delete_all()
    deletes = _ops_by_code(tl, OpCode.DELETE_NODE)
    assert len(deletes) == 3  # 2 leaves + 1 parent
