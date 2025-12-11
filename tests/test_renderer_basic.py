from __future__ import annotations

from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline
from ds_vis.core.scene.command import CommandType
from ds_vis.renderers.pyside6.renderer import COLOR_MAP, PySide6Renderer


def test_renderer_creates_node_and_positions(qt_app, scene_graph, create_cmd_factory):
    cmd = create_cmd_factory("list_render", CommandType.CREATE_STRUCTURE, kind="list")
    timeline = scene_graph.apply_command(cmd)

    scene = QGraphicsScene()
    renderer = PySide6Renderer(scene)
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
    renderer = PySide6Renderer(scene)
    renderer.render_timeline(timeline)

    node = renderer._nodes.get("node_a")
    assert node is not None
    assert node.ellipse.brush().color() == COLOR_MAP["active"]


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
    renderer = PySide6Renderer(scene)
    renderer.render_timeline(timeline)

    edge = renderer._edges.get("e1")
    assert edge is not None
    line: QGraphicsLineItem = edge.line
    assert line.line().x1() == 10.0
    assert line.line().x2() == 110.0
