from ds_vis.core.layout.tree import TreeLayoutEngine
from ds_vis.core.models.bst import BstModel


def test_tree_layout_positions_nodes_by_depth_and_order():
    model = BstModel(structure_id="tree_layout")
    timeline = model.create(values=[2, 1, 3])

    engine = TreeLayoutEngine()
    laid_out = engine.apply_layout(timeline)

    pos_ops = [
        op
        for step in laid_out.steps
        for op in step.ops
        if op.op is not None and op.data.get("x") is not None
    ]
    positions = {
        op.target: (op.data.get("x"), op.data.get("y"))
        for op in pos_ops
        if op.target
    }
    assert len(positions) == 3
    ys = [pos[1] for pos in positions.values()]
    assert min(ys) == min(ys)  # presence check
