import pytest

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import CommandType
from ds_vis.persistence.json_io import commands_from_json, commands_to_json


def test_roundtrip_json_commands(create_cmd_factory):
    cmds = [
        create_cmd_factory(
            "s1", CommandType.CREATE_STRUCTURE, kind="list", values=[1, 2]
        ),
        create_cmd_factory(
            "s1", CommandType.INSERT, kind="list", index=1, value=3
        ),
    ]
    text = commands_to_json(cmds)
    parsed = commands_from_json(text)

    assert len(parsed) == 2
    assert parsed[0].type is CommandType.CREATE_STRUCTURE
    assert parsed[0].payload["values"] == [1, 2]
    assert parsed[1].payload["index"] == 1


def test_invalid_json_raises_command_error():
    with pytest.raises(CommandError, match="Invalid JSON"):
        commands_from_json("not json")


def test_missing_kind_raises():
    bad = '[{"structure_id": "s", "type": "CREATE_STRUCTURE", "payload": {}}]'
    with pytest.raises(CommandError, match="payload.kind"):
        commands_from_json(bad)


def test_scene_persistence_roundtrip(tmp_path):
    from ds_vis.persistence.json_io import load_scene_from_file, save_scene_to_file

    scene_data = {
        "version": "1.0",
        "structures": [{"id": "l1", "kind": "list", "state": {"values": [1, 2]}}],
    }
    file_path = tmp_path / "scene.json"
    save_scene_to_file(scene_data, file_path)

    loaded_data = load_scene_from_file(file_path)
    assert loaded_data == scene_data
