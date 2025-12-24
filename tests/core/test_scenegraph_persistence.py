import pytest

from ds_vis.core.ops import OpCode
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.scene_graph import SceneGraph


def test_scenegraph_export_import_roundtrip(scene_graph):
    # 1. Setup a scene with multiple structures
    scene_graph.apply_command(
        Command("l1", CommandType.CREATE_STRUCTURE, {"kind": "list", "values": [1, 2]})
    )
    scene_graph.apply_command(
        Command(
            "b1", CommandType.CREATE_STRUCTURE, {"kind": "bst", "values": [10, 5, 15]}
        )
    )

    # 2. Export
    data = scene_graph.export_scene()
    assert data["version"] == "1.0"
    assert len(data["structures"]) == 2

    # 3. Import into a new SceneGraph
    new_sg = SceneGraph()
    tl = new_sg.import_scene(data)

    # 4. Verify
    assert "l1" in new_sg._structures
    assert "b1" in new_sg._structures
    assert new_sg._structures["l1"].values == [1, 2]
    # BST pre-order of [10, 5, 15] is [10, 5, 15]
    assert new_sg._structures["b1"].export_state()["values"] == [10, 5, 15]

    # Verify timeline has CREATE_NODE ops
    all_ops = [op for step in tl.steps for op in step.ops]
    assert any(
        op.op is OpCode.CREATE_NODE and op.data.get("structure_id") == "l1"
        for op in all_ops
    )
    assert any(
        op.op is OpCode.CREATE_NODE and op.data.get("structure_id") == "b1"
        for op in all_ops
    )


def test_import_robustness_on_failure(scene_graph):
    # 1. Setup initial state
    scene_graph.apply_command(
        Command("l1", CommandType.CREATE_STRUCTURE, {"kind": "list", "values": [1]})
    )

    # 2. Try to import invalid data
    invalid_data = {
        "version": "1.0",
        "structures": [{"id": "fail", "kind": "non_existent_kind", "state": {}}],
    }

    with pytest.raises(Exception):
        scene_graph.import_scene(invalid_data)

    # 3. Verify original state is restored
    assert "l1" in scene_graph._structures
    assert scene_graph._structures["l1"].values == [1]


def test_git_persistence_roundtrip(scene_graph):
    # 1. Setup Git
    scene_graph.apply_command(
        Command("g1", CommandType.CREATE_STRUCTURE, {"kind": "git"})
    )
    scene_graph.apply_command(
        Command("g1", CommandType.INSERT, {"kind": "git", "message": "first"})
    )
    
    # 2. Export
    data = scene_graph.export_scene()
    
    # 3. Import
    new_sg = SceneGraph()
    new_sg.import_scene(data)
    
    # 4. Verify
    g1 = new_sg._structures["g1"]
    assert len(g1.commits) == 1
    assert "c0" in g1.commits
    assert g1.commits["c0"].message == "first"
    assert g1.head == "main"
    assert g1.branches["main"] == "c0"
