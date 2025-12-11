import os

import pytest
from PySide6.QtWidgets import QApplication

from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.scene_graph import SceneGraph


@pytest.fixture
def scene_graph():
    """Returns a fresh SceneGraph instance for each test."""
    return SceneGraph()

@pytest.fixture
def create_cmd_factory():
    """Helper to create commands easily."""
    def _create(structure_id: str, cmd_type: CommandType, **payload):
        return Command(structure_id=structure_id, type=cmd_type, payload=payload)
    return _create


@pytest.fixture(scope="session")
def qt_app():
    """
    Ensure a QApplication exists for Qt graphics classes.

    Kept session-scoped to avoid repeated global init/teardown.
    """
    # Headless-friendly default.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
