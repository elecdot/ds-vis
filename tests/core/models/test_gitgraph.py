import pytest

from ds_vis.core.exceptions import ModelError
from ds_vis.core.models.gitgraph import GitGraphModel
from ds_vis.core.ops import OpCode


def _ops_by_code(timeline, code: OpCode):
    return [
        op for step in timeline.steps for op in step.ops if op.op is code
    ]


def test_git_init_and_commit():
    model = GitGraphModel(structure_id="git1")
    tl_init = model.git_init()
    creates = _ops_by_code(tl_init, OpCode.CREATE_NODE)
    assert any(op.target == "branch_main" for op in creates)
    assert any(op.target == "HEAD" for op in creates)

    tl_commit = model.commit("first")
    commit_nodes = _ops_by_code(tl_commit, OpCode.CREATE_NODE)
    assert any(op.data.get("kind") == "commit" for op in commit_nodes)
    assert model.node_count == 1


def test_git_checkout_branch_and_detached():
    model = GitGraphModel(structure_id="git2")
    model.git_init()
    model.commit("c1")
    tl_checkout = model.checkout("main")
    assert any(
        op.op is OpCode.SET_LABEL for step in tl_checkout.steps for op in step.ops
    )
    tl_detached = model.checkout("c0")
    assert any(
        op.op is OpCode.SET_LABEL for step in tl_detached.steps for op in step.ops
    )


def test_git_commit_without_init_errors():
    model = GitGraphModel(structure_id="git3")
    with pytest.raises(ModelError):
        model.commit("fail")
