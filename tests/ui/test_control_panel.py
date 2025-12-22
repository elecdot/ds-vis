from ds_vis.ui.main_window import MainWindow


def _drain(window: MainWindow) -> None:
    window._pause()
    while window._current_step_index < len(window._pending_steps):
        window._advance_step(schedule_next=False)


def test_control_panel_create_list(qt_app):
    """
    Control panel should create and render a list via SceneGraph/layout/renderer.
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._structure_id_input.setText("ui_panel_list")
        window._kind_combo.setCurrentText("list")
        window._values_input.setText("1,2,3")
        window._on_create_clicked()
        _drain(window)
        assert len(window._renderer._nodes) == 3
    finally:
        window.close()


def test_control_panel_insert_then_search(qt_app):
    """
    Control panel insert/search operations should not raise and leave nodes rendered.
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._structure_id_input.setText("ui_panel_bst")
        window._kind_combo.setCurrentText("bst")
        window._values_input.setText("5")
        window._on_create_clicked()
        _drain(window)
        window._value_input.setText("7")
        window._on_insert_clicked()
        _drain(window)
        window._value_input.setText("7")
        window._on_search_clicked()
        _drain(window)
        assert len(window._renderer._nodes) >= 2
    finally:
        window.close()
