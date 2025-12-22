from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.scene_graph import SceneGraph


def test_layout_routing_by_kind():
    sg = SceneGraph()
    list_cmd = Command(
        "list_routing",
        CommandType.CREATE_STRUCTURE,
        payload={"kind": "list", "values": [1]},
    )
    bst_cmd = Command(
        "bst_routing",
        CommandType.CREATE_STRUCTURE,
        payload={"kind": "bst", "values": [2]},
    )

    list_tl = sg.apply_command(list_cmd)
    bst_tl = sg.apply_command(bst_cmd)

    list_y = {
        op.data.get("y")
        for step in list_tl.steps
        for op in step.ops
        if op.op.name == "SET_POS"
    }
    bst_y = {
        op.data.get("y")
        for step in bst_tl.steps
        for op in step.ops
        if op.op.name == "SET_POS"
    }
    assert list_y and bst_y
    assert list_y != bst_y  # should be offset to avoid overlap
