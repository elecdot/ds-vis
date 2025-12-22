from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from PySide6.QtGui import QColor, QPen
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
)

from ds_vis.core.ops import AnimationOp, AnimationStep, OpCode, Timeline
from ds_vis.renderers.base import Renderer


@dataclass
class RendererConfig:
    """Renderer configuration (visuals + animation parameters)."""

    node_radius: float = 20.0
    rect_width: float = 48.0
    rect_height: float = 24.0
    colors: Dict[str, QColor] = field(
        default_factory=lambda: {
            "normal": QColor("#6b7280"),     # gray
            "active": QColor("#2563eb"),     # blue
            "highlight": QColor("#f59e0b"),  # amber
            "secondary": QColor("#059669"),  # green
            "to_delete": QColor("#dc2626"),  # red
            "faded": QColor("#9ca3af"),      # light gray
            "error": QColor("#f97316"),      # orange
        }
    )
    max_frames: int = 10
    show_messages: bool = True

    # Placeholder for future easing/animation parameters.
    easing: str = "linear"


@dataclass
class NodeVisual:
    """Lightweight holder for node visuals."""

    item: QGraphicsItem
    label: Optional[QGraphicsSimpleTextItem] = None
    shape: str = "circle"
    width: float = 0.0
    height: float = 0.0


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
      - Supports basic timing-aware playback: SET_POS interpolation,
        SET_STATE color interpolation, fade-in on create and fade-out on delete.
      - Minimal visuals: circles for nodes, straight lines for edges, simple labels.
    """

    def __init__(
        self,
        scene: QGraphicsScene,
        animations_enabled: bool = True,
        config: Optional[RendererConfig] = None,
    ) -> None:
        self._scene = scene
        self._nodes: Dict[str, NodeVisual] = {}
        self._edges: Dict[str, EdgeVisual] = {}
        self._message: str = ""
        self._config = config or RendererConfig()
        self._message_item = QGraphicsSimpleTextItem("")
        self._message_item.setVisible(False)
        self._message_item.setPos(10, 10)
        self._scene.addItem(self._message_item)
        self._animations_enabled: bool = animations_enabled
        self._speed_factor: float = 1.0
        self._abort_animations: bool = False

    def render_timeline(self, timeline: Timeline) -> None:
        """Interpret the given Timeline and update the scene accordingly."""
        for step in timeline.steps:
            self.apply_step(step)

    def apply_step(self, step: AnimationStep) -> None:
        if self._animations_enabled and step.duration_ms > 0:
            self._apply_step_animated(step)
        else:
            for op in step.ops:
                self._apply_op(op)

    def set_speed(self, factor: float) -> None:
        """Adjust animation speed (scales duration)."""
        self._speed_factor = max(0.1, factor)

    def set_animations_enabled(self, enabled: bool) -> None:
        """Enable or disable animations without rebuilding renderer."""
        self._animations_enabled = enabled

    def set_show_messages(self, enabled: bool) -> None:
        """Enable or disable message rendering."""
        self._config.show_messages = enabled
        if not enabled:
            self._clear_message()

    def abort_animations(self) -> None:
        """Signal any in-flight animation loop to stop safely."""
        self._abort_animations = True

    def clear(self) -> None:
        """Remove all rendered node/edge visuals and reset transient state."""
        for node in list(self._nodes.values()):
            self._scene.removeItem(node.item)
        for edge in list(self._edges.values()):
            self._scene.removeItem(edge.line)
            if edge.label:
                self._scene.removeItem(edge.label)
        self._nodes.clear()
        self._edges.clear()
        self._clear_message()

    # ------------------------------------------------------------------ #
    # Animation helpers
    # ------------------------------------------------------------------ #
    def _apply_step_animated(self, step: AnimationStep) -> None:
        """
        Basic synchronous animation:
          - SET_POS interpolated linearly
          - SET_STATE color interpolation
          - CREATE_* fade-in; DELETE_* fade-out then remove
        """
        if self._abort_animations:
            return

        adjusted_duration = int(step.duration_ms / self._speed_factor)
        frames = max(1, min(10, adjusted_duration // 50 or 1))
        create_nodes: list[AnimationOp] = []
        create_edges: list[AnimationOp] = []
        delete_nodes: list[AnimationOp] = []
        delete_edges: list[AnimationOp] = []
        set_pos_ops: list[AnimationOp] = []
        set_state_ops: list[AnimationOp] = []
        set_label_ops: list[AnimationOp] = []
        other_ops: list[AnimationOp] = []

        for op in step.ops:
            if op.op is OpCode.CREATE_NODE:
                create_nodes.append(op)
            elif op.op is OpCode.CREATE_EDGE:
                create_edges.append(op)
            elif op.op is OpCode.DELETE_NODE:
                delete_nodes.append(op)
            elif op.op is OpCode.DELETE_EDGE:
                delete_edges.append(op)
            elif op.op is OpCode.SET_POS:
                set_pos_ops.append(op)
            elif op.op is OpCode.SET_STATE:
                set_state_ops.append(op)
            elif op.op is OpCode.SET_LABEL:
                set_label_ops.append(op)
            else:
                other_ops.append(op)

        # Apply creates up front with zero opacity for fade-in.
        created_node_ids = {op.target for op in create_nodes if op.target}
        for op in create_nodes:
            self._apply_op(op)
            node = self._nodes.get(op.target or "")
            if node:
                node.item.setOpacity(0.0)
                if node.label:
                    node.label.setOpacity(0.0)

        # Pre-position newly created nodes if they have a SET_POS in this step.
        # This prevents them from "flying in" from (0,0).
        for op in set_pos_ops:
            if op.target in created_node_ids:
                self._apply_op(op)

        for op in create_edges:
            self._apply_op(op)
            edge = self._edges.get(op.target or "")
            if edge:
                edge.line.setOpacity(0.0)
                if edge.label:
                    edge.label.setOpacity(0.0)

        # Capture start/end values.
        pos_targets: Dict[str, tuple[float, float]] = {}
        pos_starts: Dict[str, tuple[float, float]] = {}
        for op in set_pos_ops:
            target = op.target or ""
            node = self._nodes.get(target)
            if node:
                pos_starts[target] = (node.item.pos().x(), node.item.pos().y())
                pos_targets[target] = (
                    float(op.data.get("x", 0.0)),
                    float(op.data.get("y", 0.0)),
                )

        state_targets: Dict[str, QColor] = {}
        state_starts: Dict[str, QColor] = {}
        for op in set_state_ops:
            target = op.target or ""
            desired = self._config.colors.get(
                op.data.get("state", "normal"), self._config.colors["normal"]
            )
            node = self._nodes.get(target)
            edge = self._edges.get(target)
            if node:
                state_starts[target] = node.item.brush().color()  # type: ignore[arg-type]
                state_targets[target] = desired
            elif edge:
                state_starts[target] = edge.line.pen().color()
                state_targets[target] = desired

        # Fade-out start values for deletes.
        delete_opacity: Dict[str, float] = {}
        for op in delete_nodes:
            target = op.target or ""
            node = self._nodes.get(target)
            if node:
                delete_opacity[target] = node.item.opacity()
        for op in delete_edges:
            target = op.target or ""
            edge = self._edges.get(target)
            if edge:
                delete_opacity[target] = edge.line.opacity()

        # Run interpolation frames synchronously (with a small wait per frame
        # so the UI can present motion when running in the main loop).
        delay_per_frame = int(adjusted_duration / frames) if frames > 0 else 0
        for i in range(1, frames + 1):
            if self._abort_animations:
                return
            t = i / frames
            # positions
            for target, end_pos in pos_targets.items():
                start_pos = pos_starts.get(target, end_pos)
                new_x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
                new_y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
                node = self._nodes.get(target)
                if node:
                    node.item.setPos(new_x, new_y)
                    self._update_edges_for_node(target)
            # states
            for target, end_color in state_targets.items():
                start_color = state_starts.get(target, end_color)
                interp = self._interpolate_color(start_color, end_color, t)
                node = self._nodes.get(target)
                if node:
                    node.item.setBrush(interp)  # type: ignore[arg-type]
                edge = self._edges.get(target)
                if edge:
                    edge.line.setPen(QPen(interp))
            # fade in/out
            for op in create_nodes:
                node = self._nodes.get(op.target or "")
                if node:
                    node.item.setOpacity(t)
                    if node.label:
                        node.label.setOpacity(t)
            for op in create_edges:
                edge = self._edges.get(op.target or "")
                if edge:
                    edge.line.setOpacity(t)
                    if edge.label:
                        edge.label.setOpacity(t)
            for op in delete_nodes:
                node = self._nodes.get(op.target or "")
                if node:
                    start_opacity = delete_opacity.get(op.target or "", 1.0)
                    node.item.setOpacity(max(0.0, start_opacity * (1 - t)))
                    if node.label:
                        node.label.setOpacity(max(0.0, start_opacity * (1 - t)))
            for op in delete_edges:
                edge = self._edges.get(op.target or "")
                if edge:
                    start_opacity = delete_opacity.get(op.target or "", 1.0)
                    edge.line.setOpacity(max(0.0, start_opacity * (1 - t)))
                    if edge.label:
                        edge.label.setOpacity(max(0.0, start_opacity * (1 - t)))
            if delay_per_frame > 0:
                QTest.qWait(delay_per_frame)
                if self._abort_animations:
                    return

        # Finalize state: apply labels, final set_state/set_label/pos just in case.
        if self._abort_animations:
            return
        for op in set_label_ops:
            self._apply_op(op)
        for op in set_state_ops:
            self._apply_op(op)
        for op in set_pos_ops:
            self._apply_op(op)
        # Remove deleted objects after fade-out.
        for op in delete_edges:
            self._delete_edge(op)
        for op in delete_nodes:
            self._delete_node(op)
        # Apply any remaining ops (messages, etc.).
        for op in other_ops:
            self._apply_op(op)

    @staticmethod
    def _interpolate_color(start: QColor, end: QColor, t: float) -> QColor:
        inv = 1.0 - t
        r = int(start.red() * inv + end.red() * t)
        g = int(start.green() * inv + end.green() * t)
        b = int(start.blue() * inv + end.blue() * t)
        a = int(start.alpha() * inv + end.alpha() * t)
        return QColor(r, g, b, a)

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
            if self._config.show_messages:
                self._set_message(op)
            return
        if op.op is OpCode.CLEAR_MESSAGE:
            if self._config.show_messages:
                self._clear_message()
            return

    def _create_node(self, op: AnimationOp) -> None:
        if not op.target:
            return

        if op.target in self._nodes:
            return  # Already exists; avoid duplicates.

        shape = str(op.data.get("shape", "circle"))
        if shape not in {"circle", "rect", "bucket"}:
            shape = "circle"

        item: QGraphicsItem
        width = float(op.data.get("width", self._config.rect_width))
        height = float(op.data.get("height", self._config.rect_height))
        if shape == "circle":
            radius = self._config.node_radius
            item = QGraphicsEllipseItem(-radius, -radius, radius * 2, radius * 2)
        else:
            # rect/bucket are centered on origin to keep setPos as center placement
            item = QGraphicsRectItem(-width / 2, -height / 2, width, height)
            # buckets keep transparent fill with colored border
            if shape == "bucket":
                pen = QPen(self._config.colors["normal"])
                pen.setWidth(2)
                item.setPen(pen)
                item.setBrush(QColor(0, 0, 0, 0))
        # default brush
        if shape != "bucket":
            item.setBrush(self._config.colors["normal"])
        self._scene.addItem(item)

        label_text = op.data.get("label")
        label_item: Optional[QGraphicsSimpleTextItem] = None
        if label_text:
            label_item = QGraphicsSimpleTextItem(str(label_text))
            label_item.setParentItem(item)
            label_rect = label_item.boundingRect()
            label_item.setPos(-label_rect.width() / 2, -label_rect.height() / 2)

        self._nodes[op.target] = NodeVisual(
            item=item, label=label_item, shape=shape, width=width, height=height
        )

    def _delete_node(self, op: AnimationOp) -> None:
        if not op.target:
            return

        node = self._nodes.pop(op.target, None)
        if node:
            self._scene.removeItem(node.item)
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
        node.item.setPos(x, y)
        # label is parented, so it moves with the node item automatically
        self._update_edges_for_node(op.target or "")

    def _set_state(self, op: AnimationOp) -> None:
        state = op.data.get("state", "normal")
        node = self._nodes.get(op.target or "")
        if node:
            color = self._config.colors.get(state, self._config.colors["normal"])
            node.item.setBrush(color)  # type: ignore[arg-type]
            return

        edge = self._edges.get(op.target or "")
        if edge:
            color = self._config.colors.get(state, self._config.colors["normal"])
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
        if not self._message:
            self._message_item.setVisible(False)
            return
        x = op.data.get("x")
        y = op.data.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            self._message_item.setPos(float(x), float(y))
        else:
            anchor_x, anchor_y = self._compute_message_anchor()
            self._message_item.setPos(anchor_x, anchor_y)
        self._message_item.setVisible(True)

    def _clear_message(self) -> None:
        self._message = ""
        self._message_item.setText("")
        self._message_item.setVisible(False)

    def _compute_message_anchor(self) -> tuple[float, float]:
        """
        Place messages near the top of current content to reduce遮挡.
        Falls back to (10,10) when scene is empty.
        """
        margin = 12.0
        content_rect = self._scene.itemsBoundingRect()
        if content_rect.isNull():
            return margin, margin
        msg_rect = self._message_item.boundingRect()
        x = content_rect.center().x() - msg_rect.width() / 2
        y = content_rect.top() - msg_rect.height() - margin
        if y < margin:
            y = content_rect.top() + margin
        return x, y

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

        src_pos = src_node.item.pos()
        dst_pos = dst_node.item.pos()
        edge.line.setLine(src_pos.x(), src_pos.y(), dst_pos.x(), dst_pos.y())

        if edge.label:
            mid_x = (src_pos.x() + dst_pos.x()) / 2
            mid_y = (src_pos.y() + dst_pos.y()) / 2
            edge.label.setPos(mid_x, mid_y)
