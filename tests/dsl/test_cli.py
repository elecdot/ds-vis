from ds_vis.dsl.cli import run_cli


def test_cli_runs_commands_from_file(tmp_path, capsys):
    text = (
        '[{"structure_id": "s1", "type": "CREATE_STRUCTURE", '
        '"payload": {"kind": "list", "values": [1, 2]}}]'
    )
    cmd_file = tmp_path / "cmds.json"
    cmd_file.write_text(text, encoding="utf-8")

    code = run_cli(["--file", str(cmd_file)])

    out = capsys.readouterr().out
    assert "Executed 1 command" in out
    assert code == 0


def test_cli_returns_error_on_invalid_text(capsys):
    code = run_cli(["--text", "not json"])

    err = capsys.readouterr().err
    assert "Error:" in err
    assert code == 1
