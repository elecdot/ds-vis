from ds_vis.core.scene.command import CommandType
from ds_vis.dsl.parser import parse_dsl


def test_parse_dsl_with_existing_kinds():
    # Scenario: L1 already exists as a list, S1 as a stack
    existing = {"L1": "list", "S1": "stack"}
    
    # Command without explicit kind
    text = "insert L1 1 5; push S1 10"
    cmds = parse_dsl(text, existing_kinds=existing)
    
    assert len(cmds) == 2
    
    assert cmds[0].structure_id == "L1"
    assert cmds[0].type == CommandType.INSERT
    assert cmds[0].payload["kind"] == "list"
    assert cmds[0].payload["value"] == 5
    
    assert cmds[1].structure_id == "S1"
    # push is mapped to INSERT in parser for stack
    assert cmds[1].type == CommandType.INSERT
    assert cmds[1].payload["kind"] == "stack"
    assert cmds[1].payload["value"] == 10

def test_parse_dsl_mixed_new_and_existing():
    existing = {"L1": "list"}
    text = "insert L1 0 1; bst B1 = [5]; search B1 5"
    cmds = parse_dsl(text, existing_kinds=existing)
    
    assert len(cmds) == 3
    assert cmds[0].payload["kind"] == "list"
    assert cmds[1].payload["kind"] == "bst"
    # B1 kind should be inferred from previous stmt
    assert cmds[2].payload["kind"] == "bst"

def test_parse_dsl_unknown_kind_omits_kind_for_scenegraph_resolution():
    # New behavior: if kind is unknown to DSL parser, it's omitted
    # so SceneGraph can resolve it from existing structures.
    text = "insert UnknownID 0 1"
    cmds = parse_dsl(text)
    assert "kind" not in cmds[0].payload

def test_robust_tokenization():
    # Test cases that used to fail or produce wrong IDs
    text1 = "list L1=[1,2]"
    cmds1 = parse_dsl(text1)
    assert cmds1[0].structure_id == "L1"
    assert cmds1[0].payload["values"] == [1, 2]
    
    text2 = "list L2 = [1, 2]"
    cmds2 = parse_dsl(text2)
    assert cmds2[0].structure_id == "L2"
    assert cmds2[0].payload["values"] == [1, 2]

