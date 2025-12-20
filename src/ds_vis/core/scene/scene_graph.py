from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from ds_vis.core.exceptions import CommandError
from ds_vis.core.layout import LayoutEngine
from ds_vis.core.layout.simple import SimpleLayoutEngine
from ds_vis.core.models import BaseModel, ListModel
from ds_vis.core.ops import Timeline

from .command import Command, CommandType
from .command_schema import MODEL_OP_REGISTRY, SCHEMA_REGISTRY


@dataclass
class SceneGraph:
    """
    Central state/scene manager.

    Responsibilities:
      - Maintain all active data-structure model instances.
      - Accept high-level Command objects from UI/DSL.
      - Dispatch to the appropriate model.
      - Collect a structural Timeline (no coordinates).
      - Pass the Timeline through layout (core.layout) before handing it to a renderer.

    P0.3: commands are routed via a handler registry; surface-only support for list
    CREATE_STRUCTURE / DELETE_STRUCTURE / DELETE_NODE. Unknown commands raise
    CommandError (no silent no-op).
    """

    _structures: Dict[str, BaseModel] = field(default_factory=dict)
    _layout_engine: Optional[LayoutEngine] = None
    _handlers: Dict[CommandType, Callable[[Command], Timeline]] = field(
        default_factory=dict
    )
    _model_registry: Dict[Tuple[str, str], Callable[[str], BaseModel]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        # Default to a simple linear layout to keep the pipeline connected.
        if self._layout_engine is None:
            self._layout_engine = SimpleLayoutEngine()
        self._register_handlers()
        self._register_models()

    def _register_handlers(self) -> None:
        self._handlers = {
            CommandType.CREATE_STRUCTURE: self._handle_create_structure,
            CommandType.DELETE_STRUCTURE: self._handle_delete_structure,
            CommandType.DELETE_NODE: self._handle_delete_node,
            CommandType.INSERT: self._handle_insert,
        }

    def apply_command(self, command: Command) -> Timeline:
        """
        Apply a high-level command and return a Timeline describing the animation.

        Current Phase:
          - CREATE_STRUCTURE (list) with minimal payload validation.
          - DELETE_STRUCTURE / DELETE_NODE for list (no legacy DELETE overload).
          - Unsupported commands raise CommandError (no silent no-op).
        """
        handler = self._handlers.get(command.type)
        if handler is None:
            raise CommandError(f"Unsupported command type: {command.type!s}")
        structural_timeline = handler(command)

        if self._layout_engine:
            return self._layout_engine.apply_layout(structural_timeline)

        return structural_timeline

    def _handle_create_structure(self, command: Command) -> Timeline:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._get_or_create_model(kind, command.structure_id)
        values = payload.get("values")
        if model.node_count:
            delete_tl = model.apply_operation("delete_all", {})
            create_tl = model.apply_operation(op_name, {"values": values})
            return self._merge_timelines(delete_tl, create_tl)
        return model.apply_operation(op_name, {"values": values})

    def _handle_delete_structure(self, command: Command) -> Timeline:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None or model.kind != kind:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        return model.apply_operation(op_name, payload)

    def _handle_delete_node(self, command: Command) -> Timeline:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None or model.kind != kind:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        index = payload.get("index")
        if isinstance(index, int) and (index < 0 or index >= model.node_count):
            raise CommandError("DELETE_NODE index out of range")
        return model.apply_operation(op_name, {"index": index})

    def _handle_insert(self, command: Command) -> Timeline:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None or model.kind != kind:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        index = payload.get("index")
        if isinstance(index, int) and (index < 0 or index > model.node_count):
            raise CommandError("INSERT index out of range")
        return model.apply_operation(
            op_name, {"index": index, "value": payload.get("value")}
        )

    def _merge_timelines(self, *timelines: Timeline) -> Timeline:
        merged = Timeline()
        for tl in timelines:
            for step in tl.steps:
                merged.add_step(step)
        return merged

    # ------------------------------------------------------------------ #
    # Model registry + schema helpers
    # ------------------------------------------------------------------ #
    def _register_models(self) -> None:
        self._model_registry = {
            ("list", "list"): lambda structure_id: self._get_or_create_list_model(
                structure_id
            ),
        }

    def _get_or_create_model(self, kind: str, structure_id: str) -> BaseModel:
        key = (kind, kind)
        factory = self._model_registry.get(key)
        if factory is None:
            raise CommandError(f"No model registered for kind: {kind!r}")
        existing = self._structures.get(structure_id)
        if existing:
            return existing
        model = factory(structure_id)
        self._structures[structure_id] = model
        return model

    def _resolve_schema_and_op(
        self, command: Command
    ) -> Tuple[str, str, Mapping[str, Any]]:
        payload = command.payload
        if not isinstance(payload, Mapping):
            raise CommandError("Command payload must be a mapping")
        kind = payload.get("kind")
        if not isinstance(kind, str):
            raise CommandError("Command requires payload.kind as string")

        schema = SCHEMA_REGISTRY.get((command.type, kind))
        if schema is None:
            raise CommandError(f"Unsupported command/kind combination: {kind!r}")
        schema.validate(payload)

        op_name = MODEL_OP_REGISTRY.get((command.type, kind))
        if op_name is None:
            raise CommandError(f"Unsupported operation for kind: {kind!r}")
        return kind, op_name, payload

    def _get_or_create_list_model(self, structure_id: str) -> ListModel:
        existing = self._structures.get(structure_id)
        if isinstance(existing, ListModel):
            return existing

        model = ListModel(structure_id=structure_id)
        self._structures[structure_id] = model
        return model
