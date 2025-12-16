from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsScene,
    QGraphicsView,
    QMainWindow,
    QMenu,
    QMenuBar,
    QToolBar,
)

from ds_vis.core.ops import AnimationStep, Timeline
from ds_vis.core.scene import SceneGraph
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.renderers.pyside6.renderer import PySide6Renderer

# Developer examples (structural timelines only)
try:
    # Optional import; if examples are missing, the Dev menu will be disabled.
    from ds_vis.examples.timelines import (
        bst_insert_7_into_root_5,
        bst_insert_7_with_layout_example,
    )
except ImportError:  # pragma: no cover - defensive
    bst_insert_7_into_root_5 = None  # type: ignore[assignment]
    bst_insert_7_with_layout_example = None  # type: ignore[assignment]

class MainWindow(QMainWindow):
    """
    Minimal main window for the visualizer.

    Phase 1:
      - Sets up a basic QGraphicsView and wires a SceneGraph + Renderer.
      - Adds a small 'Dev' menu entry to inspect example Timelines and
        run a list creation through the full stack.
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
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_step)
        self._pending_steps: list[AnimationStep] = []
        self._current_step_index: int = 0
        self._speed_factor: float = 1.0
        self._animations_enabled: bool = True

        # Developer playground menu
        self._init_menubar()
        self._init_toolbar()

    # --------------------------------------------------------------------- #
    # UI setup
    # --------------------------------------------------------------------- #

    def _init_menubar(self) -> None:
        """Initialize a minimal menubar with a 'Dev' menu."""
        menubar: QMenuBar = self.menuBar()

        dev_menu: QMenu = menubar.addMenu("Dev")

        # Dev -> Run BST Insert Example (with layout injection)
        self._act_run_bst_example = QAction(
            "Run BST Insert Example (print to console)", self
        )
        self._act_run_bst_example.triggered.connect(self._run_bst_example)
        self._act_run_bst_example.setEnabled(bst_insert_7_into_root_5 is not None)

        dev_menu.addAction(self._act_run_bst_example)

        # Dev -> Create List via full pipeline
        # (Command -> SceneGraph -> Layout -> Renderer)
        self._act_create_list = QAction(
            "Create List (render)", self
        )
        self._act_create_list.triggered.connect(self._create_list_dev)
        dev_menu.addAction(self._act_create_list)

        self._act_list_insert = QAction(
            "Play List Insert (1,3 -> insert 2)", self
        )
        self._act_list_insert.triggered.connect(self._play_list_insert_dev)
        dev_menu.addAction(self._act_list_insert)

    def _init_toolbar(self) -> None:
        """Playback controls toolbar."""
        toolbar = QToolBar("Playback", self)
        self.addToolBar(toolbar)

        self._act_play = QAction("Play", self)
        self._act_play.triggered.connect(self._play)
        toolbar.addAction(self._act_play)

        self._act_pause = QAction("Pause", self)
        self._act_pause.triggered.connect(self._pause)
        toolbar.addAction(self._act_pause)

        self._act_step = QAction("Step", self)
        self._act_step.triggered.connect(self._step_once)
        toolbar.addAction(self._act_step)

        speed_menu = QMenu("Speed", self)
        for label, factor in [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]:
            action = QAction(label, self)
            action.triggered.connect(lambda _=False, f=factor: self._set_speed(f))
            speed_menu.addAction(action)
        speed_button = QAction("Speed", self)
        speed_button.setMenu(speed_menu)
        toolbar.addAction(speed_button)

        self._act_toggle_anim = QAction("Animations", self, checkable=True)
        self._act_toggle_anim.setChecked(True)
        self._act_toggle_anim.triggered.connect(self._toggle_animations)
        toolbar.addAction(self._act_toggle_anim)

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

        timeline = bst_insert_7_with_layout_example()

        print("\n=== Dev: BST insert example timeline ===")
        for i, step in enumerate(timeline.steps, start=1):
            print(f"Step {i}: duration={step.duration_ms} ms, label={step.label!r}")
            for op in step.ops:
                # AnimationOp is a dataclass, so its repr is readable enough for dev.
                print("   ", op)
        print("=== End of example ===\n")

        # Forward this to the renderer for visual inspection:
        self._renderer.render_timeline(timeline)

    def _create_list_dev(self) -> None:
        """
        Developer-only hook: create a list structure through the full pipeline.

        Command -> SceneGraph (structural ops) -> Layout (inject SET_POS) -> Renderer.
        """
        self._reset_engine()
        cmd = Command(
            structure_id="dev_list",
            type=CommandType.CREATE_STRUCTURE,
            payload={"kind": "list", "values": [1, 2, 3]},
        )
        timeline = self._scene_graph.apply_command(cmd)
        # Phase 1: render immediately; future phases may add animation controls.
        self._renderer.render_timeline(timeline)

    def _play_list_insert_dev(self) -> None:
        """
        Developer-only hook: demonstrate L2 list insert with highlight micro-steps.
        """
        self._reset_engine()
        structure_id = "dev_list_insert"
        create_cmd = Command(
            structure_id=structure_id,
            type=CommandType.CREATE_STRUCTURE,
            payload={"kind": "list", "values": [1, 3]},
        )
        insert_cmd = Command(
            structure_id=structure_id,
            type=CommandType.INSERT,
            payload={"kind": "list", "index": 1, "value": 2},
        )
        create_tl = self._scene_graph.apply_command(create_cmd)
        insert_tl = self._scene_graph.apply_command(insert_cmd)

        merged = Timeline()
        for step in list(create_tl.steps) + list(insert_tl.steps):
            merged.add_step(step)

        self._play_timeline(merged)

    def _reset_engine(self) -> None:
        """Reset scene, renderer, and scene graph for a fresh demo run."""
        self._timer.stop()
        self._pending_steps = []
        self._current_step_index = 0
        self._scene.clear()
        self._scene_graph = SceneGraph()
        self._renderer = PySide6Renderer(
            self._scene, animations_enabled=self._animations_enabled
        )
        self._renderer.set_speed(self._speed_factor)

    def _play_timeline(self, timeline: Timeline) -> None:
        """Play a timeline step-by-step using the renderer and a timer."""
        self._timer.stop()
        self._pending_steps = list(timeline.steps)
        self._current_step_index = 0
        if not self._pending_steps:
            return
        self._advance_step()

    def _advance_step(self, schedule_next: bool = True) -> None:
        if self._current_step_index >= len(self._pending_steps):
            self._timer.stop()
            return

        step = self._pending_steps[self._current_step_index]
        self._renderer.apply_step(step)
        self._current_step_index += 1
        if schedule_next and self._current_step_index < len(self._pending_steps):
            delay = int(max(0, step.duration_ms) / self._speed_factor)
            self._timer.start(delay)
        else:
            self._timer.stop()

    def _play(self) -> None:
        if not self._pending_steps:
            return
        # If paused mid-sequence, resume; otherwise restart from current index.
        if not self._timer.isActive():
            current = max(0, min(self._current_step_index, len(self._pending_steps)))
            if current >= len(self._pending_steps):
                self._current_step_index = 0
            self._advance_step()

    def _pause(self) -> None:
        self._timer.stop()

    def _step_once(self) -> None:
        self._timer.stop()
        self._advance_step(schedule_next=False)

    def _set_speed(self, factor: float) -> None:
        self._speed_factor = max(0.1, factor)
        self._renderer.set_speed(self._speed_factor)

    def _toggle_animations(self, checked: bool) -> None:
        self._animations_enabled = checked
        self._renderer.set_animations_enabled(checked)

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
