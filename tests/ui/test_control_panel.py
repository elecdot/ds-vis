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


def test_control_panel_create_seqlist_with_bucket(qt_app):
    """
    Seqlist renders rectangular cells with bucket container (shape=bucket).
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._structure_id_input.setText("ui_panel_seq")
        window._kind_combo.setCurrentText("seqlist")
        window._values_input.setText("1,2")
        window._on_create_clicked()
        _drain(window)
        shapes = {visual.shape for visual in window._renderer._nodes.values()}
        assert "rect" in shapes
        assert "bucket" in shapes
    finally:
        window.close()


def test_control_panel_stack_push_pop(qt_app):
    """
    Stack push/pop routes through SceneGraph and keeps bucket + cells rendered.
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._structure_id_input.setText("ui_stack")
        window._kind_combo.setCurrentText("stack")
        window._values_input.setText("1,2")
        window._on_create_clicked()
        _drain(window)
        base_shapes = {visual.shape for visual in window._renderer._nodes.values()}
        assert "bucket" in base_shapes

        window._value_input.setText("3")
        window._on_insert_clicked()
        _drain(window)
        rect_count = sum(
            1 for visual in window._renderer._nodes.values() if visual.shape == "rect"
        )
        assert rect_count >= 2

        window._on_delete_clicked()
        _drain(window)
        shapes_after_pop = {visual.shape for visual in window._renderer._nodes.values()}
        assert "bucket" in shapes_after_pop
    finally:
        window.close()


def test_control_panel_git_commit_checkout(qt_app):
    """
    Git commit/checkout routes without crash; HEAD label exists.
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        window._structure_id_input.setText("ui_git")
        window._kind_combo.setCurrentText("git")
        window._on_create_clicked()
        _drain(window)
        window._value_input.setText("msg1")
        window._on_insert_clicked()
        _drain(window)
        window._value_input.setText("main")
        window._on_search_clicked()
        _drain(window)
        assert "HEAD" in window._renderer._nodes
        head_node = window._renderer._nodes["HEAD"].item
        commits = [
            n.item
            for nid, n in window._renderer._nodes.items()
            if n.shape == "circle"
        ]
        assert commits
        # HEAD 应靠近最新 commit
        commit_pos = commits[-1].pos()
        head_pos = head_node.pos()
        assert abs(head_pos.x() - commit_pos.x()) < 1e-3
        assert head_pos.y() < commit_pos.y()
    finally:
        window.close()


def test_control_panel_run_dsl_text_multi_structures(qt_app):
    """
    DSL 文本入口应能创建并渲染多个结构。
    """
    window = MainWindow()
    window._toggle_animations(False)
    window._set_speed(100.0)
    try:
        dsl_text = "list L1 = [1,2]; stack S1 = [3]; insert L1 1 9"
        window._run_dsl_text(dsl_text)
        _drain(window)
        # 两个结构至少生成 3 个节点
        assert len(window._renderer._nodes) >= 3
    finally:
        window.close()
