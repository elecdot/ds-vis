from __future__ import annotations

from PySide6.QtWidgets import QGraphicsEllipseItem

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
