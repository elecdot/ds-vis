from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
)

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline
from ds_vis.renderers.base import Renderer

# Basic visual constants for Phase 1 renderer.
NODE_RADIUS = 20.0
COLOR_MAP: Dict[str, QColor] = {
    "normal": QColor("#6b7280"),     # gray
    "active": QColor("#2563eb"),     # blue
    "secondary": QColor("#059669"),  # green
    "to_delete": QColor("#dc2626"),  # red
    "faded": QColor("#9ca3af"),      # light gray
    "error": QColor("#f97316"),      # orange
}


@dataclass
class NodeVisual:
    """Lightweight holder for node visuals."""

    ellipse: QGraphicsEllipseItem
    label: Optional[QGraphicsSimpleTextItem] = None


@dataclass
class EdgeVisual:
    """Lightweight holder for edge visuals."""

    line: QGraphicsLineItem
    label: Optional[QGraphicsSimpleTextItem] = None
    src_id: str = ""
    dst_id: str = ""


class PySide6Renderer(Renderer):
    """
    PySide6-based renderer using QGraphicsScene/QGraphicsView.

    Phase 1:
      - No animation timing; apply final state of each step immediately.
      - Minimal visuals: circles for nodes, straight lines for edges, simple labels.
    """

    def __init__(self, scene: QGraphicsScene) -> None:
        self._scene = scene
        self._nodes: Dict[str, NodeVisual] = {}
        self._edges: Dict[str, EdgeVisual] = {}
        self._message: str = ""
        self._message_item = QGraphicsSimpleTextItem("")
        self._message_item.setVisible(False)
        self._message_item.setPos(10, 10)
        self._scene.addItem(self._message_item)

    def render_timeline(self, timeline: Timeline) -> None:
        """Interpret the given Timeline and update the scene accordingly."""
        for step in timeline.steps:
            self.apply_step(step)

    def apply_step(self, step: AnimationStep) -> None:
        for op in step.ops:
            self._apply_op(op)

    def _apply_op(self, op: AnimationOp) -> None:
        if op.op is OpCode.CREATE_NODE:
            self._create_node(op)
            return
        if op.op is OpCode.DELETE_NODE:
            self._delete_node(op)
            return
        if op.op is OpCode.CREATE_EDGE:
            self._create_edge(op)
            return
        if op.op is OpCode.DELETE_EDGE:
            self._delete_edge(op)
            return
        if op.op is OpCode.SET_POS:
            self._set_pos(op)
            return
        if op.op is OpCode.SET_STATE:
            self._set_state(op)
            return
        if op.op is OpCode.SET_LABEL:
            self._set_label(op)
            return
        if op.op is OpCode.SET_MESSAGE:
            self._set_message(op)
            return
        if op.op is OpCode.CLEAR_MESSAGE:
            self._clear_message()
            return

    def _create_node(self, op: AnimationOp) -> None:
        if not op.target:
            return

        if op.target in self._nodes:
            return  # Already exists; avoid duplicates.

        ellipse = QGraphicsEllipseItem(
            -NODE_RADIUS,
            -NODE_RADIUS,
            NODE_RADIUS * 2,
            NODE_RADIUS * 2,
        )
        ellipse.setBrush(COLOR_MAP["normal"])
        self._scene.addItem(ellipse)

        label_text = op.data.get("label")
        label_item: Optional[QGraphicsSimpleTextItem] = None
        if label_text:
            label_item = QGraphicsSimpleTextItem(str(label_text))
            label_item.setParentItem(ellipse)
            label_item.setPos(-NODE_RADIUS / 2, -NODE_RADIUS / 2)

        self._nodes[op.target] = NodeVisual(ellipse=ellipse, label=label_item)

    def _delete_node(self, op: AnimationOp) -> None:
        if not op.target:
            return

        node = self._nodes.pop(op.target, None)
        if node:
            self._scene.removeItem(node.ellipse)
        # Remove edges connected to this node.
        for edge_id, edge in list(self._edges.items()):
            if edge.src_id == op.target or edge.dst_id == op.target:
                self._scene.removeItem(edge.line)
                self._edges.pop(edge_id, None)

    def _create_edge(self, op: AnimationOp) -> None:
        if not op.target:
            return
        if op.target in self._edges:
            return

        src = op.data.get("from")
        dst = op.data.get("to")
        line = QGraphicsLineItem()
        line.setPen(QPen(QColor("#111827")))
        self._scene.addItem(line)

        label_text = op.data.get("label")
        label_item = None
        if label_text:
            label_item = QGraphicsSimpleTextItem(str(label_text))
            self._scene.addItem(label_item)

        self._edges[op.target] = EdgeVisual(
            line=line,
            label=label_item,
            src_id=src or "",
            dst_id=dst or "",
        )

        self._update_edge_position(op.target)

    def _delete_edge(self, op: AnimationOp) -> None:
        if not op.target:
            return

        edge = self._edges.pop(op.target, None)
        if edge:
            self._scene.removeItem(edge.line)
            if edge.label:
                self._scene.removeItem(edge.label)

    def _set_pos(self, op: AnimationOp) -> None:
        node = self._nodes.get(op.target or "")
        if not node:
            return
        x = float(op.data.get("x", 0.0))
        y = float(op.data.get("y", 0.0))
        node.ellipse.setPos(x, y)
        # label is parented, so it moves with ellipse automatically
        self._update_edges_for_node(op.target or "")

    def _set_state(self, op: AnimationOp) -> None:
        state = op.data.get("state", "normal")
        node = self._nodes.get(op.target or "")
        if node:
            color = COLOR_MAP.get(state, COLOR_MAP["normal"])
            node.ellipse.setBrush(color)
            return

        edge = self._edges.get(op.target or "")
        if edge:
            color = COLOR_MAP.get(state, COLOR_MAP["normal"])
            edge.line.setPen(QPen(color))

    def _set_label(self, op: AnimationOp) -> None:
        node = self._nodes.get(op.target or "")
        if node and node.label:
            node.label.setText(str(op.data.get("text", "")))
            return

        edge = self._edges.get(op.target or "")
        if edge and edge.label:
            edge.label.setText(str(op.data.get("text", "")))
            self._update_edge_position(op.target or "")

    def _set_message(self, op: AnimationOp) -> None:
        self._message = str(op.data.get("text", ""))
        self._message_item.setText(self._message)
        self._message_item.setVisible(bool(self._message))

    def _clear_message(self) -> None:
        self._message = ""
        self._message_item.setText("")
        self._message_item.setVisible(False)

    def _update_edges_for_node(self, node_id: str) -> None:
        for edge_id, edge in self._edges.items():
            if edge.src_id == node_id or edge.dst_id == node_id:
                self._update_edge_position(edge_id)

    def _update_edge_position(self, edge_id: str) -> None:
        edge = self._edges.get(edge_id)
        if not edge:
            return

        src_node = self._nodes.get(edge.src_id)
        dst_node = self._nodes.get(edge.dst_id)
        if not src_node or not dst_node:
            return

        src_pos = src_node.ellipse.pos()
        dst_pos = dst_node.ellipse.pos()
        edge.line.setLine(src_pos.x(), src_pos.y(), dst_pos.x(), dst_pos.y())

        if edge.label:
            mid_x = (src_pos.x() + dst_pos.x()) / 2
            mid_y = (src_pos.y() + dst_pos.y()) / 2
            edge.label.setPos(mid_x, mid_y)
