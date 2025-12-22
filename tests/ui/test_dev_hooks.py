from __future__ import annotations

from PySide6.QtWidgets import QGraphicsEllipseItem, QInputDialog

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.ui.main_window import MainWindow


def test_dev_create_list_renders_scene(qt_app):
    """
    Smoke test: dev hook should render a list with multiple nodes and layout.
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._create_list_dev()

    ellipse_items = [
        item
        for item in window._scene.items()
        if isinstance(item, QGraphicsEllipseItem)
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
    window._toggle_animations(False)
    try:
        window._create_list_dev()
        initial_ids = set(window._renderer._nodes.keys())

        delete_cmd = Command(
            structure_id="dev_list",
            type=CommandType.DELETE_STRUCTURE,
            payload={"kind": "list"},
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
            (node.item.pos().x(), node.item.pos().y())
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


def test_dev_play_list_insert_demo_runs_all_steps(qt_app):
    """
    Ensure the dev demo for list insert plays through and leaves nodes in normal state.
    """
    window = MainWindow()
    window._toggle_animations(True)
    window._set_speed(100.0)
    try:
        window._play_list_insert_dev()
        window._pause()
        while window._current_step_index < len(window._pending_steps):
            window._advance_step(schedule_next=False)

        nodes = window._renderer._nodes
        assert len(nodes) == 3
        assert all(
            visual.item.brush().color()
            == window._renderer._config.colors["normal"]
            for visual in nodes.values()
        )
    finally:
        window.close()


def test_toggle_messages_disables_message_render(qt_app):
    window = MainWindow()
    window._toggle_animations(False)
    try:
        window._toggle_messages(False)
        step = AnimationStep(
            ops=[
                AnimationOp(
                    op=OpCode.SET_MESSAGE,
                    target=None,
                    data={"text": "hidden"},
                )
            ]
        )
        window._renderer.apply_step(step)
        assert not window._renderer._message_item.isVisible()
    finally:
        window.close()


def test_dev_play_list_full_demo_runs_without_residual_nodes(qt_app):
    """
    Full ListModel demo should run all operations and end with an empty scene.
    """
    window = MainWindow()
    window._toggle_animations(True)
    window._set_speed(100.0)
    try:
        window._play_list_full_demo()
        window._pause()
        while window._current_step_index < len(window._pending_steps):
            window._advance_step(schedule_next=False)

        assert not window._renderer._nodes
        assert not window._renderer._edges
    finally:
        window.close()


def test_playback_controls_respect_speed(qt_app):
    """
    Speed factor should scale the timer delay; simulate by stepping manually.
    """
    window = MainWindow()
    window._toggle_animations(False)
    try:
        window._play_list_insert_dev()
        window._set_speed(2.0)
        # Advance first step; timer would schedule next with halved delay.
        window._advance_step()
        assert window._timer.interval() == int(
            max(0, window._pending_steps[0].duration_ms) / window._speed_factor
        )
    finally:
        window.close()


def test_step_does_not_reschedule_timer(qt_app):
    """
    After pause, stepping once should not re-arm the timer (blocking mode).
    """
    window = MainWindow()
    window._toggle_animations(False)
    try:
        window._play_list_insert_dev()
        window._pause()
        previous_index = window._current_step_index
        window._step_once()
        assert not window._timer.isActive()
        assert window._current_step_index == previous_index + 1
    finally:
        window.close()


def test_dev_run_dsl_input_runs_commands(qt_app, monkeypatch):
    """
    DSL/JSON input hook should parse commands and render them.
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        text = (
            '[{"structure_id": "dsl_list", "type": "CREATE_STRUCTURE", '
            '"payload": {"kind": "list", "values": [5, 6]}}]'
        )
        monkeypatch.setattr(
            QInputDialog,
            "getMultiLineText",
            staticmethod(lambda *_, **__: (text, True)),
        )
        window._run_dsl_input_dev()
        window._pause()
        while window._current_step_index < len(window._pending_steps):
            window._advance_step(schedule_next=False)

        assert len(window._renderer._nodes) == 2
    finally:
        window.close()


def test_dev_bst_demo_runs(qt_app):
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._play_bst_demo()
        window._pause()
        while window._current_step_index < len(window._pending_steps):
            window._advance_step(schedule_next=False)
        # bst demo inserts root + two children => 3 nodes
        assert len(window._renderer._nodes) == 3
    finally:
        window.close()


def test_dev_bst_full_demo_runs(qt_app):
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._play_bst_full_demo()
        window._pause()
        while window._current_step_index < len(window._pending_steps):
            window._advance_step(schedule_next=False)
        # after deletions, should have remaining nodes (root replaced)
        assert window._renderer._nodes
    finally:
        window.close()
