import pytest

from ds_vis.core.scene.command import CommandType
from ds_vis.dsl.parser import parse_dsl


def test_parse_create_and_insert_text():
    text = "list L1 = [1,2]; insert L1 1 5; search L1 val=5"
    cmds = parse_dsl(text)
    assert cmds[0].type is CommandType.CREATE_STRUCTURE
    assert cmds[0].payload["values"] == [1, 2]
    assert cmds[1].type is CommandType.INSERT
    assert cmds[1].payload["value"] == 5
    assert cmds[2].type is CommandType.SEARCH
    assert cmds[2].payload["value"] == 5


def test_parse_stack_push_pop():
    text = "stack S1 = [1]; push S1 2; pop S1"
    cmds = parse_dsl(text)
    assert cmds[0].payload["kind"] == "stack"
    assert cmds[1].payload["value"] == 2
    assert cmds[2].type is CommandType.DELETE_NODE


def test_parse_git_commands():
    text = 'git G1 init; commit G1 "m1"; checkout G1 main'
    cmds = parse_dsl(text)
    assert cmds[0].payload["kind"] == "git"
    assert cmds[1].payload["message"] == "m1"
    assert cmds[2].payload["target"] == "main"


def test_invalid_statement_raises():
    with pytest.raises(Exception):
        parse_dsl("unknown op")


def test_bst_search_uses_value():
    text = "bst B1 = [5,3,7]; search B1 7"
    cmds = parse_dsl(text)
    assert cmds[1].payload["kind"] == "bst"
    assert "value" in cmds[1].payload
    assert "index" not in cmds[1].payload
