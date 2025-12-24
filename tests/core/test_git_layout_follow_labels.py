from ds_vis.core.ops import OpCode
from ds_vis.core.scene.command import CommandType


def _latest_positions(timeline):
    positions = {}
    for step in timeline.steps:
        for op in step.ops:
            if op.op is OpCode.SET_POS and op.target:
                positions.setdefault(op.target, []).append(
                    (op.data.get("x"), op.data.get("y"))
                )
    return {k: v[-1] for k, v in positions.items()}


def test_git_labels_follow_commit(scene_graph, create_cmd_factory):
    scene_graph.apply_command(
        create_cmd_factory("git_lay", CommandType.CREATE_STRUCTURE, kind="git")
    )

    commit1 = scene_graph.apply_command(
        create_cmd_factory("git_lay", CommandType.INSERT, kind="git", message="first")
    )
    pos1 = _latest_positions(commit1)
    assert "c0" in pos1
    # HEAD / branch anchor to commit vertically above
    assert pos1["branch_main"][0] == pos1["c0"][0]
    assert pos1["HEAD"][0] == pos1["c0"][0]
    assert pos1["branch_main"][1] < pos1["c0"][1]
    assert pos1["HEAD"][1] < pos1["c0"][1]

    commit2 = scene_graph.apply_command(
        create_cmd_factory("git_lay", CommandType.INSERT, kind="git", message="second")
    )
    pos2 = _latest_positions(commit2)
    assert "c1" in pos2
    # labels move with the new HEAD position
    assert pos2["branch_main"][0] == pos2["c1"][0]
    assert pos2["HEAD"][0] == pos2["c1"][0]
    assert pos2["branch_main"][1] < pos2["c1"][1]
    assert pos2["branch_main"] != pos1["branch_main"]
    assert pos2["HEAD"] != pos1["HEAD"]
