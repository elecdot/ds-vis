from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QMainWindow
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QScreen

from ds_vis.core.scene import SceneGraph
from ds_vis.renderers.pyside6.renderer import PySide6Renderer


class MainWindow(QMainWindow):
    """
    Minimal main window for the visualizer.

    Phase 0: only sets up a basic QGraphicsView and wires a SceneGraph + Renderer,
    without any actual controls or animations.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Data Structure Visualizer (MVP Skeleton)")
        
        # Set window size to 60% of screen size (DPI-aware)
        screen: QScreen | None = self.screen()
        if screen:
            available_geometry = screen.availableGeometry()
            width = int(available_geometry.width() * 0.6)
            height = int(available_geometry.height() * 0.6)
            self.resize(width, height)
        else:
            # Fallback if screen info unavailable
            self.resize(960, 720)

        self._scene = QGraphicsScene(self)
        self._view = QGraphicsView(self._scene, self)
        self._view.setRenderHint(self._view.renderHints())
        self._view.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.setCentralWidget(self._view)

        # Core engine wiring (skeleton)
        self._scene_graph = SceneGraph()
        self._renderer = PySide6Renderer(self._scene)


def main() -> None:
    """
    Entry point for launching the desktop MVP skeleton.

    Usage (from project root):

        uv run python -m ds_vis.ui.main_window
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
