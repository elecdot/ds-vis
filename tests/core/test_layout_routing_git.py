from ds_vis.core.layout import LayoutStrategy
from ds_vis.core.scene.scene_graph import SceneGraph


def test_git_layout_strategy_and_config():
    sg = SceneGraph()
    assert sg._layout_map["git"] is LayoutStrategy.DAG
    cfg = sg._kind_layout_config["git"]
    assert cfg["orientation"] == "vertical"
