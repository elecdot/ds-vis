from __future__ import annotations

import sys
from typing import Any, Dict, List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QScreen
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ds_vis.core.exceptions import CommandError
from ds_vis.core.ops import AnimationStep, Timeline
from ds_vis.core.scene import SceneGraph
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.dsl.parser import parse_dsl
from ds_vis.persistence.json_io import (
    load_scene_from_file,
    save_scene_to_file,
)
from ds_vis.renderers.pyside6.renderer import PySide6Renderer, RendererConfig

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
        self._control_panel = self._build_control_panel()
        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self._control_panel)
        splitter.addWidget(self._view)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        # Core engine wiring (skeleton)
        self._scene_graph = SceneGraph()
        self._renderer = PySide6Renderer(self._scene)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance_step)
        self._pending_steps: list[AnimationStep] = []
        self._current_step_index: int = 0
        self._speed_factor: float = 1.0
        self._animations_enabled: bool = True
        self._show_messages: bool = True
        self._paused: bool = False

        # Developer playground menu
        self._init_menubar()
        self._init_toolbar()
        self._wire_control_panel()

    # --------------------------------------------------------------------- #
    # UI setup
    # --------------------------------------------------------------------- #
    def _build_control_panel(self) -> QWidget:
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        form_layout = QVBoxLayout()
        self._structure_id_input = QLineEdit("ui_ds", panel)
        self._kind_combo = QComboBox(panel)
        self._kind_combo.addItems(["list", "seqlist", "stack", "bst", "huffman", "git"])
        self._values_input = QLineEdit("", panel)
        self._value_input = QLineEdit("", panel)
        self._index_input = QLineEdit("", panel)

        def add_row(label_text: str, widget: QWidget) -> None:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text, panel))
            row.addWidget(widget)
            form_layout.addLayout(row)

        add_row("Structure ID", self._structure_id_input)
        add_row("Kind", self._kind_combo)
        add_row("Values (comma)", self._values_input)
        add_row("Value", self._value_input)
        add_row("Index", self._index_input)

        layout.addLayout(form_layout)

        btn_create = QPushButton("Create", panel)
        btn_insert = QPushButton("Insert", panel)
        btn_search = QPushButton("Search", panel)
        btn_delete = QPushButton("Delete", panel)
        btn_delete_all = QPushButton("Delete All", panel)
        btn_dsl = QPushButton("Run DSL/JSON", panel)
        btn_import = QPushButton("Import JSON", panel)
        btn_export = QPushButton("Export JSON", panel)

        for btn in [
            btn_create,
            btn_insert,
            btn_search,
            btn_delete,
            btn_delete_all,
            btn_dsl,
            btn_import,
            btn_export,
        ]:
            btn.setMinimumHeight(28)
            layout.addWidget(btn)

        layout.addStretch(1)
        self._btn_create = btn_create
        self._btn_insert = btn_insert
        self._btn_search = btn_search
        self._btn_delete = btn_delete
        self._btn_delete_all = btn_delete_all
        self._btn_dsl = btn_dsl
        self._btn_import = btn_import
        self._btn_export = btn_export
        self._kind_combo.currentTextChanged.connect(self._update_controls_for_kind)
        return panel

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

        self._act_list_full = QAction(
            "Play List Full Demo (create/insert/search/update/delete)", self
        )
        self._act_list_full.triggered.connect(self._play_list_full_demo)
        dev_menu.addAction(self._act_list_full)

        self._act_run_dsl = QAction("Run DSL/JSON (input)", self)
        self._act_run_dsl.triggered.connect(self._run_dsl_input_dev)
        dev_menu.addAction(self._act_run_dsl)

        self._act_bst_demo = QAction("Play BST Demo (create/insert)", self)
        self._act_bst_demo.triggered.connect(self._play_bst_demo)
        dev_menu.addAction(self._act_bst_demo)

        self._act_bst_full = QAction(
            "Play BST Full Demo (search/delete)", self
        )
        self._act_bst_full.triggered.connect(self._play_bst_full_demo)
        dev_menu.addAction(self._act_bst_full)

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

        self._act_toggle_message = QAction("Messages", self, checkable=True)
        self._act_toggle_message.setChecked(True)
        self._act_toggle_message.triggered.connect(self._toggle_messages)
        toolbar.addAction(self._act_toggle_message)

    def _wire_control_panel(self) -> None:
        self._btn_create.clicked.connect(self._on_create_clicked)
        self._btn_insert.clicked.connect(self._on_insert_clicked)
        self._btn_search.clicked.connect(self._on_search_clicked)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        self._btn_delete_all.clicked.connect(self._on_delete_all_clicked)
        self._btn_dsl.clicked.connect(self._run_dsl_input_dev)
        self._btn_import.clicked.connect(self._on_import_clicked)
        self._btn_export.clicked.connect(self._on_export_clicked)
        self._update_controls_for_kind()

    # --------------------------------------------------------------------- #
    # Developer playground hooks (for manual testing only)
    # --------------------------------------------------------------------- #
    def _parse_structure_id(self) -> str:
        return self._structure_id_input.text().strip() or "ui_ds"

    def _parse_kind(self) -> str:
        return self._kind_combo.currentText().strip() or "list"

    def _parse_values(self) -> List[object]:
        raw = self._values_input.text().strip()
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        parsed: List[object] = []
        for part in parts:
            if part.lstrip("-").isdigit():
                parsed.append(int(part))
            else:
                parsed.append(part)
        return parsed

    def _parse_value(self) -> Any:
        raw = self._value_input.text().strip()
        if not raw:
            return None
        return int(raw) if raw.lstrip("-").isdigit() else raw

    def _parse_index(self) -> Any:
        raw = self._index_input.text().strip()
        if not raw:
            return None
        return int(raw) if raw.lstrip("-").isdigit() else raw

    def _update_controls_for_kind(self) -> None:
        kind = self._parse_kind()
        if kind == "stack":
            self._btn_insert.setText("Push")
            self._btn_delete.setText("Pop")
            self._index_input.setPlaceholderText("Top only (ignored)")
        elif kind == "git":
            self._btn_insert.setText("Commit")
            self._btn_delete.setText("Delete")
            self._index_input.setPlaceholderText("")
        else:
            self._btn_insert.setText("Insert")
            self._btn_delete.setText("Delete")
            self._index_input.setPlaceholderText("")

    def _on_create_clicked(self) -> None:
        sid = self._parse_structure_id()
        kind = self._parse_kind()
        values = self._parse_values()
        payload: Dict[str, object] = {"kind": kind}
        if values:
            payload["values"] = values
        cmd = Command(
            sid,
            CommandType.CREATE_STRUCTURE,
            payload,
        )
        self._run_commands([cmd])

    def _on_insert_clicked(self) -> None:
        sid = self._parse_structure_id()
        kind = self._parse_kind()
        if kind == "huffman":
            QMessageBox.information(
                self, "Not Supported", "Huffman 目前仅支持创建/删除。"
            )
            return
        if kind == "git":
            payload_git: Dict[str, object] = {
                "kind": kind,
                "message": self._parse_value() or "commit",
            }
            cmd = Command(sid, CommandType.INSERT, payload_git)
            self._run_commands([cmd])
            return
        payload: Dict[str, object] = {"kind": kind, "value": self._parse_value()}
        idx = self._parse_index()
        if kind == "stack":
            if payload.get("value") is None:
                QMessageBox.warning(self, "Input Error", "Stack push requires value")
                return
            # 栈仅支持栈顶 push，忽略 index 输入避免无效 payload
        else:
            if idx is not None:
                payload["index"] = idx
        cmd = Command(sid, CommandType.INSERT, payload)
        self._run_commands([cmd])

    def _on_search_clicked(self) -> None:
        sid = self._parse_structure_id()
        kind = self._parse_kind()
        if kind == "huffman":
            QMessageBox.information(
                self, "Not Supported", "Huffman 目前仅支持创建/删除。"
            )
            return
        if kind == "git":
            target = self._parse_value()
            if not isinstance(target, str):
                QMessageBox.warning(
                    self, "Input Error", "Git checkout 需要目标分支/commit id"
                )
                return
            cmd = Command(
                sid,
                CommandType.SEARCH,
                payload={"kind": kind, "target": target},
            )
            self._run_commands([cmd])
            return
        payload: Dict[str, object] = {"kind": kind, "value": self._parse_value()}
        idx = self._parse_index()
        if idx is not None:
            payload["index"] = idx
        cmd = Command(sid, CommandType.SEARCH, payload)
        self._run_commands([cmd])

    def _on_delete_clicked(self) -> None:
        sid = self._parse_structure_id()
        kind = self._parse_kind()
        payload: Dict[str, object] = {"kind": kind}
        if kind == "stack":
            # 栈出栈始终作用于栈顶，忽略 index
            pass
        elif kind == "huffman":
            QMessageBox.information(
                self, "Not Supported", "Huffman 删除请使用 Delete All。"
            )
            return
        else:
            idx = self._parse_index()
            if idx is not None:
                payload["index"] = idx
        val = self._parse_value()
        if val is not None and kind != "stack":
            payload["value"] = val
        cmd = Command(sid, CommandType.DELETE_NODE, payload)
        self._run_commands([cmd])

    def _on_delete_all_clicked(self) -> None:
        sid = self._parse_structure_id()
        kind = self._parse_kind()
        cmd = Command(sid, CommandType.DELETE_STRUCTURE, {"kind": kind})
        self._run_commands([cmd])

    def _run_commands(self, commands: list[Command]) -> None:
        """Apply a sequence of commands and play their timelines."""
        self._timer.stop()
        merged = Timeline()
        try:
            for cmd in commands:
                tl = self._scene_graph.apply_command(cmd)
                for step in tl.steps:
                    merged.add_step(step)
        except CommandError as exc:
            QMessageBox.critical(self, "Command Error", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "Error", str(exc))
            return
        if not merged.steps:
            return
        self._play_timeline(merged)

    def _on_import_clicked(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Scene JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        try:
            scene_data = load_scene_from_file(filename)
            timeline = self._scene_graph.import_scene(scene_data)
            self._play_timeline(timeline)
        except CommandError as exc:
            QMessageBox.critical(self, "Import Error", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))
            return

    def _on_export_clicked(self) -> None:
        # Check if there are any structures to export
        if not self._scene_graph._structures:
            QMessageBox.information(
                self, "Export", "No structures in the scene to export."
            )
            return
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Scene JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        try:
            scene_data = self._scene_graph.export_scene()
            save_scene_to_file(scene_data, filename)
            QMessageBox.information(
                self, "Export", f"Exported scene state to {filename}"
            )
        except CommandError as exc:
            QMessageBox.critical(self, "Export Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))


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
            payload={"kind": "list", "values": [1, 3]}
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

    def _play_list_full_demo(self) -> None:
        """
        Developer-only hook: exercise full ListModel operations end-to-end.

        Covers: create empty (sentinel), insert head/mid/tail, search (hit/miss),
        update (by index/value), delete_index, delete_all.
        """
        self._reset_engine()
        sid = "dev_list_full"
        commands = [
            Command(sid, CommandType.CREATE_STRUCTURE, {"kind": "list", "values": []}),
            Command(sid, CommandType.INSERT, {"kind": "list", "index": 0, "value": 1}),
            Command(sid, CommandType.INSERT, {"kind": "list", "index": 1, "value": 3}),
            Command(sid, CommandType.INSERT, {"kind": "list", "index": 1, "value": 2}),
            Command(sid, CommandType.SEARCH, {"kind": "list", "value": 2}),
            Command(sid, CommandType.SEARCH, {"kind": "list", "value": 99}),
            Command(
                sid,
                CommandType.UPDATE,
                {"kind": "list", "index": 1, "new_value": 20},
            ),
            Command(
                sid,
                CommandType.UPDATE,
                {"kind": "list", "value": 3, "new_value": 30},
            ),
            Command(sid, CommandType.DELETE_NODE, {"kind": "list", "index": 0}),
            Command(sid, CommandType.DELETE_STRUCTURE, {"kind": "list"}),
        ]

        merged = Timeline()
        for cmd in commands:
            tl = self._scene_graph.apply_command(cmd)
            for step in tl.steps:
                merged.add_step(step)

        self._play_timeline(merged)

    def _run_dsl_input_dev(self) -> None:
        """
        Developer-only hook: paste DSL/JSON text, run through SceneGraph, and render.
        """
        example = (
            "list L1 = [1,2]; insert L1 1 9; "
            "stack S1 = [3]; push S1 4; "
            "bst B1 = [5,3,7]; search B1 7; "
            "git G1 init; commit G1 \"msg\""
        )
        text, ok = QInputDialog.getMultiLineText(
            self,
            "Run DSL/JSON",
            "Enter commands (JSON array or DSL text):",
            example,
        )
        if not ok or not text.strip():
            return

        self._run_dsl_text(text)

    def _run_dsl_text(self, text: str) -> None:
        self._reset_engine()
        try:
            commands = parse_dsl(text)
        except Exception as exc:  # pragma: no cover - defensive
            QMessageBox.critical(self, "DSL Error", str(exc))
            return

        merged = Timeline()
        for cmd in commands:
            tl = self._scene_graph.apply_command(cmd)
            for step in tl.steps:
                merged.add_step(step)

        self._play_timeline(merged)

    def _play_bst_demo(self) -> None:
        """
        Developer-only hook: exercise BST create/insert end-to-end.
        """
        self._reset_engine()
        sid = "dev_bst_demo"
        commands = [
            Command(
                sid,
                CommandType.CREATE_STRUCTURE,
                {"kind": "bst", "values": [5]},
            ),
            Command(
                sid,
                CommandType.INSERT,
                {"kind": "bst", "value": 3},
            ),
            Command(
                sid,
                CommandType.INSERT,
                {"kind": "bst", "value": 7},
            ),
        ]

        merged = Timeline()
        for cmd in commands:
            tl = self._scene_graph.apply_command(cmd)
            for step in tl.steps:
                merged.add_step(step)

        self._play_timeline(merged)

    def _play_bst_full_demo(self) -> None:
        """
        Developer-only hook: BST end-to-end (insert/search/delete).
        """
        self._reset_engine()
        sid = "dev_bst_full"
        commands = [
            Command(sid, CommandType.CREATE_STRUCTURE, {"kind": "bst", "values": [5]}),
            Command(sid, CommandType.INSERT, {"kind": "bst", "value": 3}),
            Command(sid, CommandType.INSERT, {"kind": "bst", "value": 7}),
            Command(sid, CommandType.INSERT, {"kind": "bst", "value": 6}),
            Command(sid, CommandType.INSERT, {"kind": "bst", "value": 2}),
            Command(sid, CommandType.INSERT, {"kind": "bst", "value": 8}),
            Command(sid, CommandType.SEARCH, {"kind": "bst", "value": 6}),
            Command(sid, CommandType.SEARCH, {"kind": "bst", "value": 9}),
            Command(sid, CommandType.DELETE_NODE, {"kind": "bst", "value": 6}),
            Command(sid, CommandType.DELETE_NODE, {"kind": "bst", "value": 3}),
            Command(sid, CommandType.DELETE_NODE, {"kind": "bst", "value": 5}),
        ]

        merged = Timeline()
        for cmd in commands:
            tl = self._scene_graph.apply_command(cmd)
            for step in tl.steps:
                merged.add_step(step)

        self._play_timeline(merged)

    def _reset_engine(self) -> None:
        """Reset scene, renderer, and scene graph for a fresh demo run."""
        self._timer.stop()
        self._pending_steps = []
        self._current_step_index = 0
        self._paused = False
        self._renderer.abort_animations()
        self._scene.clear()
        config = RendererConfig(show_messages=self._show_messages)
        self._scene_graph = SceneGraph()
        self._renderer = PySide6Renderer(
            self._scene,
            animations_enabled=self._animations_enabled,
            config=config,
        )
        self._renderer.set_speed(self._speed_factor)

    def _play_timeline(self, timeline: Timeline) -> None:
        """Play a timeline step-by-step using the renderer and a timer."""
        self._timer.stop()
        self._pending_steps = list(timeline.steps)
        self._current_step_index = 0
        self._paused = False
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
        if (
            schedule_next
            and not self._paused
            and self._current_step_index < len(self._pending_steps)
        ):
            delay = int(max(0, step.duration_ms) / self._speed_factor)
            self._timer.start(delay)
        else:
            self._timer.stop()

    def _play(self) -> None:
        if not self._pending_steps:
            return
        # If paused mid-sequence, resume; otherwise restart from current index.
        self._paused = False
        if not self._timer.isActive():
            current = max(0, min(self._current_step_index, len(self._pending_steps)))
            if current >= len(self._pending_steps):
                self._renderer.clear()
                self._current_step_index = 0
            self._advance_step()

    def _pause(self) -> None:
        self._paused = True
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

    def _toggle_messages(self, checked: bool) -> None:
        self._show_messages = checked
        self._renderer.set_show_messages(checked)

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
