from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
)

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline
from ds_vis.core.scene.command import CommandType
from ds_vis.renderers.pyside6.renderer import PySide6Renderer, RendererConfig


def test_renderer_creates_node_and_positions(qt_app, scene_graph, create_cmd_factory):
    cmd = create_cmd_factory("list_render", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)
    renderer.render_timeline(timeline)

    # At least one ellipse should be present for the sentinel node.
    ellipse_items = [
        item for item in scene.items() if isinstance(item, QGraphicsEllipseItem)
    ]
    assert ellipse_items, "No node visuals were created"

    # Position should reflect layout defaults (50, 50) for the first node.
    pos = ellipse_items[0].pos()
    assert pos.x() == 50.0
    assert pos.y() == 50.0


def test_renderer_respects_custom_config(qt_app):
    config = RendererConfig(
        node_radius=10.0,
        colors={"normal": QColor("#000000"), "active": QColor("#ffffff")},
        max_frames=5,
        show_messages=False,
    )
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="node_c",
                        data={"structure_id": "s1", "kind": "list_node", "label": "C"},
                    ),
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target="node_c",
                        data={"state": "active"},
                    ),
                    AnimationOp(
                        op=OpCode.SET_MESSAGE,
                        target=None,
                        data={"text": "Hidden"},
                    ),
                ]
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False, config=config)
    renderer.render_timeline(timeline)

    node = renderer._nodes.get("node_c")
    assert node is not None
    # radius applied (roughly equals ellipse width/2)
    assert node.ellipse.rect().width() == config.node_radius * 2
    assert node.ellipse.brush().color() == config.colors["active"]
    # message disabled
    assert not renderer._message_item.isVisible()


def test_renderer_applies_state_color(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="node_a",
                        data={"structure_id": "s1", "kind": "list_node", "label": "A"},
                    ),
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target="node_a",
                        data={"state": "active"},
                    ),
                ]
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)
    renderer.render_timeline(timeline)

    node = renderer._nodes.get("node_a")
    assert node is not None
    assert node.ellipse.brush().color() == renderer._config.colors["active"]


def test_renderer_applies_highlight_state(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="node_h",
                        data={"structure_id": "s1", "kind": "list_node", "label": "H"},
                    ),
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target="node_h",
                        data={"state": "highlight"},
                    ),
                ]
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)
    renderer.render_timeline(timeline)

    node = renderer._nodes.get("node_h")
    assert node is not None
    assert node.ellipse.brush().color() == renderer._config.colors["highlight"]


def test_renderer_applies_edge_highlight(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s1", "kind": "list_node", "label": "1"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s1", "kind": "list_node", "label": "2"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_EDGE,
                        target="e1",
                        data={"structure_id": "s1", "from": "n1", "to": "n2"},
                    ),
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target="e1",
                        data={"state": "highlight"},
                    ),
                ]
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)
    renderer.render_timeline(timeline)

    edge = renderer._edges.get("e1")
    assert edge is not None
    assert edge.line.pen().color() == renderer._config.colors["highlight"]


def test_renderer_updates_edges_on_position(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s1", "kind": "list_node", "label": "1"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s1", "kind": "list_node", "label": "2"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_EDGE,
                        target="e1",
                        data={
                            "structure_id": "s1",
                            "from": "n1",
                            "to": "n2",
                            "directed": True,
                        },
                    ),
                    AnimationOp(
                        op=OpCode.SET_POS, target="n1", data={"x": 10.0, "y": 20.0}
                    ),
                    AnimationOp(
                        op=OpCode.SET_POS, target="n2", data={"x": 110.0, "y": 20.0}
                    ),
                ]
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)
    renderer.render_timeline(timeline)

    edge = renderer._edges.get("e1")
    assert edge is not None
    line: QGraphicsLineItem = edge.line
    assert line.line().x1() == 10.0
    assert line.line().x2() == 110.0


def test_renderer_animates_position(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                duration_ms=10,
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s1", "kind": "list_node", "label": "1"},
                    ),
                    AnimationOp(
                        op=OpCode.SET_POS,
                        target="n1",
                        data={"x": 100.0, "y": 50.0},
                    ),
                ],
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=True)
    renderer.render_timeline(timeline)

    node = renderer._nodes.get("n1")
    assert node is not None
    pos = node.ellipse.pos()
    assert pos.x() == 100.0
    assert pos.y() == 50.0


def test_renderer_fade_out_delete(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s1", "kind": "list_node", "label": "1"},
                    ),
                ]
            ),
            AnimationStep(
                duration_ms=10,
                ops=[
                    AnimationOp(
                        op=OpCode.DELETE_NODE,
                        target="n1",
                        data={"structure_id": "s1"},
                    )
                ],
            ),
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=True)
    renderer.render_timeline(timeline)

    assert "n1" not in renderer._nodes


def test_renderer_color_interpolation_reaches_target(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s1", "kind": "list_node", "label": "1"},
                    )
                ]
            ),
            AnimationStep(
                duration_ms=10,
                ops=[
                    AnimationOp(
                        op=OpCode.SET_STATE,
                        target="n1",
                        data={"state": "highlight"},
                    )
                ],
            ),
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=True)
    renderer.render_timeline(timeline)

    node = renderer._nodes.get("n1")
    assert node is not None
    assert node.ellipse.brush().color() == renderer._config.colors["highlight"]


def test_renderer_sets_and_clears_message(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.SET_MESSAGE,
                        target=None,
                        data={"text": "hello world"},
                    )
                ]
            ),
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CLEAR_MESSAGE,
                        target=None,
                        data={},
                    )
                ]
            ),
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)

    renderer.apply_step(timeline.steps[0])
    assert renderer._message == "hello world"
    assert renderer._message_item.isVisible()
    assert renderer._message_item.text() == "hello world"
    assert any(
        isinstance(item, QGraphicsSimpleTextItem) and item.text() == "hello world"
        for item in scene.items()
    )

    renderer.apply_step(timeline.steps[1])
    assert renderer._message == ""
    assert renderer._message_item.text() == ""
    assert renderer._message_item.isVisible() is False


def test_renderer_clear_removes_visuals(qt_app):
    timeline = Timeline(
        steps=[
            AnimationStep(
                ops=[
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n1",
                        data={"structure_id": "s1", "kind": "list_node", "label": "1"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_NODE,
                        target="n2",
                        data={"structure_id": "s1", "kind": "list_node", "label": "2"},
                    ),
                    AnimationOp(
                        op=OpCode.CREATE_EDGE,
                        target="e1",
                        data={"structure_id": "s1", "from": "n1", "to": "n2"},
                    ),
                ]
            )
        ]
    )

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene, animations_enabled=False)
    renderer.render_timeline(timeline)

    assert renderer._nodes
    assert renderer._edges
    assert any(isinstance(item, QGraphicsEllipseItem) for item in scene.items())
    assert any(isinstance(item, QGraphicsLineItem) for item in scene.items())

    renderer.clear()

    assert not renderer._nodes
    assert not renderer._edges
    assert not any(isinstance(item, QGraphicsEllipseItem) for item in scene.items())
    assert not any(isinstance(item, QGraphicsLineItem) for item in scene.items())
