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

    assert any(
        op.data.get("y") == 50.0
        for step in list_tl.steps
        for op in step.ops
        if op.op.name == "SET_POS"
    )
    assert any(
        op.data.get("y") == 50.0
        for step in bst_tl.steps
        for op in step.ops
        if op.op.name == "SET_POS"
    )
