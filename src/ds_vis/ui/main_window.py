from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QMenu,
    QMenuBar,
)

from ds_vis.core.scene import SceneGraph
from ds_vis.renderers.pyside6.renderer import PySide6Renderer

# Developer examples (structural timelines only)
try:
    # Optional import; if examples are missing, the Dev menu will be disabled.
    from ds_vis.examples.timelines import bst_insert_7_into_root_5
except ImportError:  # pragma: no cover - defensive
    bst_insert_7_into_root_5 = None  # type: ignore[assignment]

class MainWindow(QMainWindow):
    """
    Minimal main window for the visualizer.

    Phase 1:
      - Sets up a basic QGraphicsView and wires a SceneGraph + Renderer.
      - Adds a small 'Dev' menu entry to inspect example Timelines.
        This is a developer playground only and NOT part of the core product flow.
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
        self._view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.setCentralWidget(self._view)

        # Core engine wiring (skeleton)
        self._scene_graph = SceneGraph()
        self._renderer = PySide6Renderer(self._scene)

        # Developer playground menu
        self._init_menubar()

    # --------------------------------------------------------------------- #
    # UI setup
    # --------------------------------------------------------------------- #

    def _init_menubar(self) -> None:
        """Initialize a minimal menubar with a 'Dev' menu."""
        menubar: QMenuBar = self.menuBar()

        dev_menu: QMenu = menubar.addMenu("Dev")

        # Dev -> Run BST Insert Example
        self._act_run_bst_example = QAction(
            "Run BST Insert Example (print to console)", self
        )
        self._act_run_bst_example.triggered.connect(self._run_bst_example)
        self._act_run_bst_example.setEnabled(bst_insert_7_into_root_5 is not None)

        dev_menu.addAction(self._act_run_bst_example)

    # --------------------------------------------------------------------- #
    # Developer playground hooks (for manual testing only)
    # --------------------------------------------------------------------- #

    def _run_bst_example(self) -> None:
        """
        Developer-only hook to inspect an example Timeline.

        Behavior:
          - builds the example Timeline,
          - prints its structure to stdout.
        This does NOT perform real rendering logic yet and is NOT part
        of the core application flow.
        """
        if bst_insert_7_into_root_5 is None:
            print("Example function bst_insert_7_into_root_5() not available.")
            return

        timeline = bst_insert_7_into_root_5()

        print("\n=== Dev: BST insert example timeline ===")
        for i, step in enumerate(timeline.steps, start=1):
            print(f"Step {i}: duration={step.duration_ms} ms, label={step.label!r}")
            for op in step.ops:
                # AnimationOp is a dataclass, so its repr is readable enough for dev.
                print("   ", op)
        print("=== End of example ===\n")

        # In future phases, we may forward this to the renderer:
        #   self._renderer.render_timeline(timeline)
        # For now, we keep this function as a pure inspection tool.

    # --------------------------------------------------------------------- #
    # Entry point
    # --------------------------------------------------------------------- #

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
