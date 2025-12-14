from __future__ import annotations

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


def test_dev_create_delete_recreate_stable_ids(qt_app):
    """
    Smoke: create -> delete -> recreate should avoid ID reuse and refresh layout.
    """
    window = MainWindow()
    try:
        window._create_list_dev()
        initial_ids = set(window._renderer._nodes.keys())

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

        recreated_ids = set(window._renderer._nodes.keys())
        assert initial_ids and recreated_ids
        assert initial_ids.isdisjoint(recreated_ids)

        recreated_positions = [
            (node.ellipse.pos().x(), node.ellipse.pos().y())
            for node in window._renderer._nodes.values()
        ]
        # Layout refresh should place nodes on the line with spacing.
        assert len(set(recreated_positions)) == len(recreated_positions) == len(
            recreated_ids
        )
        xs = sorted(pos[0] for pos in recreated_positions)
        assert xs[0] == 50.0
        if len(xs) > 1:
            assert xs[1] - xs[0] == 120.0
    finally:
        window.close()
