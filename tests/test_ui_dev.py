from __future__ import annotations

import pytest
from PySide6.QtWidgets import QGraphicsEllipseItem

from ds_vis.core.scene.command import Command, CommandType
from ds_vis.ui.main_window import MainWindow


def test_dev_create_list_renders_scene(qt_app):
    """
    Smoke test: dev hook should render a list with multiple nodes and layout.
    """
    window = MainWindow()
    window._create_list_dev()

    ellipse_items = [
        item for item in window._scene.items() if isinstance(item, QGraphicsEllipseItem)
    ]
    try:
        assert len(ellipse_items) == 3, "Expected three list nodes rendered"
        positions = [(item.pos().x(), item.pos().y()) for item in ellipse_items]
        # Basic layout sanity: nodes should not collapse onto the exact same point.
        assert len(set(positions)) == 3
    finally:
        window.close()


@pytest.mark.xfail(
    reason="P0.3 pending: delete/recreate with stable IDs and layout refresh"
)
def test_dev_create_delete_recreate_stable_ids(qt_app):
    """
    Future smoke: create -> delete -> recreate should keep surviving IDs stable
    and refresh layout.
    """
    window = MainWindow()
    try:
        window._create_list_dev()
        initial_ids = sorted(window._renderer._nodes.keys())
        initial_positions = {
            node_id: (
                node.ellipse.pos().x(),
                node.ellipse.pos().y(),
            )
            for node_id, node in window._renderer._nodes.items()
        }

        delete_cmd = Command(
            structure_id="dev_list",
            type=CommandType.DELETE,
            payload={},
        )
        delete_timeline = window._scene_graph.apply_command(delete_cmd)
        window._renderer.render_timeline(delete_timeline)

        recreate_cmd = Command(
            structure_id="dev_list",
            type=CommandType.CREATE_STRUCTURE,
            payload={"kind": "list", "values": [9, 8]},
        )
        recreate_timeline = window._scene_graph.apply_command(recreate_cmd)
        window._renderer.render_timeline(recreate_timeline)

        recreated_ids = sorted(window._renderer._nodes.keys())
        assert initial_ids and recreated_ids
        assert initial_ids[0] == recreated_ids[0]
        # Layout refresh should reposition nodes deterministically.
        recreated_positions = {
            node_id: (
                node.ellipse.pos().x(),
                node.ellipse.pos().y(),
            )
            for node_id, node in window._renderer._nodes.items()
        }
        assert len(set(recreated_positions.values())) == len(recreated_positions)
        assert recreated_positions != initial_positions
    finally:
        window.close()
