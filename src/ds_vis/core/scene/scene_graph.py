from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from ds_vis.core.exceptions import CommandError
from ds_vis.core.layout import DEFAULT_LAYOUT_MAP, LayoutEngine, LayoutStrategy
from ds_vis.core.layout.git import GitLayoutEngine
from ds_vis.core.layout.simple import SimpleLayoutEngine
from ds_vis.core.layout.tree import TreeLayoutEngine
from ds_vis.core.models import BaseModel
from ds_vis.core.ops import AnimationOp, AnimationStep, Timeline

from .command import Command, CommandType
from .command_schema import (
    MODEL_FACTORY_REGISTRY,
    MODEL_OP_REGISTRY,
    SCHEMA_REGISTRY,
)


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
    _tree_layout_engine: Optional[LayoutEngine] = None
    _dag_layout_engine: Optional[LayoutEngine] = None
    _layout_map: Dict[str, LayoutStrategy] = field(default_factory=dict)
    _structure_offsets: Dict[str, tuple[float, float]] = field(default_factory=dict)
    _structure_layout_config: Dict[str, Mapping[str, object]] = field(
        default_factory=dict
    )
    _row_index: Dict[LayoutStrategy, int] = field(default_factory=dict)
    _handlers: Dict[CommandType, Callable[[Command], Tuple[Timeline, str]]] = field(
        default_factory=dict
    )
    def __post_init__(self) -> None:
        # Default to a simple linear layout to keep the pipeline connected.
        if self._layout_engine is None:
            self._layout_engine = SimpleLayoutEngine()
        if self._tree_layout_engine is None:
            self._tree_layout_engine = TreeLayoutEngine()
        if self._dag_layout_engine is None:
            self._dag_layout_engine = GitLayoutEngine()
        if not self._layout_map:
            self._layout_map = dict(DEFAULT_LAYOUT_MAP)
        self._register_handlers()
        # TODO(P0.8): allow injecting/swapping layout engines/strategies and invoking
        # layout_engine.reset() on scene reset/seek to support non-linear layouts.
        # TODO(P0.8): consider layout routing (e.g., per-structure strategy selection)
        # rather than a single engine instance, once tree/DAG layouts are available.
        # Layout defaults per kind (orientation/spacing等)
        self._kind_layout_config: Dict[str, Mapping[str, object]] = {
            "seqlist": {"orientation": "horizontal", "spacing": 80.0},
            "list": {"orientation": "horizontal", "spacing": 120.0},
            "stack": {
                "orientation": "vertical",
                "spacing": 80.0,
                "row_spacing": 200.0,
            },
            "git": {"orientation": "vertical", "spacing": 140.0},
            "bst": {"spacing": 120.0, "level_spacing": 100.0},
            "huffman": {
                "queue_spacing": 80.0,
                "queue_start_y": 0.0,
                "tree_offset_y": 180.0,
                "tree_span": 240.0,
            },
        }

    def _register_handlers(self) -> None:
        self._handlers = {
            CommandType.CREATE_STRUCTURE: self._handle_create_structure,
            CommandType.DELETE_STRUCTURE: self._handle_delete_structure,
            CommandType.DELETE_NODE: self._handle_delete_node,
            CommandType.INSERT: self._handle_insert,
            CommandType.SEARCH: self._handle_search,
            CommandType.UPDATE: self._handle_update,
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
        structural_timeline, kind = handler(command)

        return self._apply_layout(kind, structural_timeline)

    def _handle_create_structure(self, command: Command) -> Tuple[Timeline, str]:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._get_or_create_model(kind, command.structure_id)
        values = payload.get("values")
        if model.node_count:
            delete_tl = model.apply_operation("delete_all", {})
            create_tl = model.apply_operation(op_name, {"values": values})
            merged = self._merge_timelines(delete_tl, create_tl)
            return merged, kind
        return model.apply_operation(op_name, {"values": values}), kind

    def _handle_delete_structure(self, command: Command) -> Tuple[Timeline, str]:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        if model.kind != kind:
            raise CommandError(
                f"Kind mismatch for {command.structure_id!r}: "
                f"expected {kind}, found {model.kind}"
            )
        return model.apply_operation(op_name, payload), kind

    def _handle_delete_node(self, command: Command) -> Tuple[Timeline, str]:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        if model.kind != kind:
            raise CommandError(
                f"Kind mismatch for {command.structure_id!r}: "
                f"expected {kind}, found {model.kind}"
            )
        if kind == "bst":
            value = payload.get("value")
            return model.apply_operation(op_name, {"value": value}), kind
        index = payload.get("index")
        if isinstance(index, int) and (index < 0 or index >= model.node_count):
            raise CommandError("DELETE_NODE index out of range")
        return model.apply_operation(op_name, {"index": index}), kind

    def _handle_insert(self, command: Command) -> Tuple[Timeline, str]:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        if model.kind != kind:
            raise CommandError(
                f"Kind mismatch for {command.structure_id!r}: "
                f"expected {kind}, found {model.kind}"
            )
        if kind == "git":
            message = payload.get("message") or payload.get("value")
            return model.apply_operation(op_name, {"message": message}), kind
        index = payload.get("index")
        if isinstance(index, int) and (index < 0 or index > model.node_count):
            raise CommandError("INSERT index out of range")
        return (
            model.apply_operation(
                op_name, {"index": index, "value": payload.get("value")}
            ),
            kind,
        )

    def _handle_search(self, command: Command) -> Tuple[Timeline, str]:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        if model.kind != kind:
            raise CommandError(
                f"Kind mismatch for {command.structure_id!r}: "
                f"expected {kind}, found {model.kind}"
            )
        if kind == "git":
            target = payload.get("target")
            return model.apply_operation(op_name, {"target": target}), kind
        if kind == "bst":
            return model.apply_operation(op_name, {"value": payload.get("value")}), kind
        index = payload.get("index")
        if isinstance(index, int) and (index < 0 or index >= model.node_count):
            raise CommandError("SEARCH index out of range")
        return (
            model.apply_operation(
                op_name, {"index": index, "value": payload.get("value")}
            ),
            kind,
        )

    def _handle_update(self, command: Command) -> Tuple[Timeline, str]:
        kind, op_name, payload = self._resolve_schema_and_op(command)
        model = self._structures.get(command.structure_id)
        if model is None:
            raise CommandError(f"Structure not found: {command.structure_id!r}")
        if model.kind != kind:
            raise CommandError(
                f"Kind mismatch for {command.structure_id!r}: "
                f"expected {kind}, found {model.kind}"
            )
        index = payload.get("index")
        if isinstance(index, int) and (index < 0 or index >= model.node_count):
            raise CommandError("UPDATE index out of range")
        return (
            model.apply_operation(
                op_name,
                {
                    "index": index,
                    "value": payload.get("value"),
                    "new_value": payload.get("new_value"),
                },
            ),
            kind,
        )

    def export_scene(self) -> Mapping[str, object]:
        """
        Export the entire scene state (all structures, offsets, and configs).
        """
        structures = []
        for sid, model in self._structures.items():
            structures.append(
                {
                    "id": sid,
                    "kind": model.kind,
                    "state": model.export_state(),
                    "offset": self._structure_offsets.get(sid),
                    "config": self._structure_layout_config.get(sid),
                }
            )
        return {"version": "1.0", "structures": structures}

    def import_scene(self, data: Mapping[str, object]) -> Timeline:
        """
        Clear the current scene and restore from a snapshot.
        Robustness: validates all structures before modifying current state.
        """
        if not isinstance(data, Mapping) or data.get("version") != "1.0":
            raise CommandError("Invalid scene data version")

        structures_data = data.get("structures")
        if not isinstance(structures_data, list):
            raise CommandError("Invalid scene data: structures must be a list")

        # 1. Dry run: validate and prepare new state
        new_structures: Dict[str, BaseModel] = {}
        new_offsets: Dict[str, Tuple[float, float]] = {}
        new_configs: Dict[str, Mapping[str, object]] = {}
        create_timelines: List[Timeline] = []

        for s_data in structures_data:
            if not isinstance(s_data, Mapping):
                continue
            sid = s_data.get("id")
            kind = s_data.get("kind")
            state = s_data.get("state")
            offset = s_data.get("offset")
            config = s_data.get("config")

            if not isinstance(sid, str) or not isinstance(kind, str):
                raise CommandError(
                    "Invalid structure data: id and kind must be strings"
                )

            factory = MODEL_FACTORY_REGISTRY.get(kind)
            if factory is None:
                raise CommandError(f"No model registered for kind: {kind!r}")

            model = factory(sid)
            try:
                tl = model.apply_operation("create", state or {})
                create_timelines.append(tl)
            except Exception as e:
                raise CommandError(
                    f"Failed to restore state for {sid} ({kind}): {e}"
                ) from e

            new_structures[sid] = model
            if isinstance(offset, (list, tuple)) and len(offset) == 2:
                new_offsets[sid] = (float(offset[0]), float(offset[1]))

            if isinstance(config, Mapping):
                new_configs[sid] = config

        # 2. Commit: generate delete ops for old state and swap
        delete_ops: List[AnimationOp] = []
        for sid, model in self._structures.items():
            tl = model.apply_operation("delete_all", {})
            for step in tl.steps:
                delete_ops.extend(step.ops)

        self._structures = new_structures
        self._structure_offsets = new_offsets
        self._structure_layout_config = new_configs
        self._row_index.clear()

        # Re-assign offsets for those that didn't have them
        for sid, model in self._structures.items():
            if sid not in self._structure_offsets:
                self._assign_offset(sid, model.kind)

        # 3. Return merged timeline
        timeline = Timeline()
        if delete_ops:
            timeline.add_step(AnimationStep(ops=delete_ops, label="Clear scene"))

        for tl in create_timelines:
            for step in tl.steps:
                timeline.add_step(step)

        return self._apply_layout_to_import(timeline)

    def _apply_layout_to_import(self, timeline: Timeline) -> Timeline:
        """
        Apply all layout engines to a mixed-structure timeline.
        """
        tl = timeline

        # Filter SIDs by strategy to avoid interference
        linear_sids = {
            sid
            for sid, m in self._structures.items()
            if self._layout_map.get(m.kind) == LayoutStrategy.LINEAR
        }
        tree_sids = {
            sid
            for sid, m in self._structures.items()
            if self._layout_map.get(m.kind) == LayoutStrategy.TREE
        }
        dag_sids = {
            sid
            for sid, m in self._structures.items()
            if self._layout_map.get(m.kind) == LayoutStrategy.DAG
        }

        # Run engines sequentially; later engines (Tree/DAG) override earlier ones
        if self._layout_engine:
            self._layout_engine.reset()
            if hasattr(self._layout_engine, "set_filter"):
                self._layout_engine.set_filter(linear_sids)
            if hasattr(self._layout_engine, "set_offsets"):
                self._layout_engine.set_offsets(self._structure_offsets)
            if hasattr(self._layout_engine, "set_structure_config"):
                self._layout_engine.set_structure_config(self._structure_layout_config)
            tl = self._layout_engine.apply_layout(tl)

        if self._tree_layout_engine:
            self._tree_layout_engine.reset()
            if hasattr(self._tree_layout_engine, "set_filter"):
                self._tree_layout_engine.set_filter(tree_sids)
            if hasattr(self._tree_layout_engine, "set_offsets"):
                self._tree_layout_engine.set_offsets(self._structure_offsets)
            if hasattr(self._tree_layout_engine, "set_structure_config"):
                self._tree_layout_engine.set_structure_config(
                    self._structure_layout_config
                )
            tl = self._tree_layout_engine.apply_layout(tl)

        if self._dag_layout_engine:
            self._dag_layout_engine.reset()
            if hasattr(self._dag_layout_engine, "set_filter"):
                self._dag_layout_engine.set_filter(dag_sids)
            if hasattr(self._dag_layout_engine, "set_offsets"):
                self._dag_layout_engine.set_offsets(self._structure_offsets)
            tl = self._dag_layout_engine.apply_layout(tl)
        return tl

    def _merge_timelines(self, *timelines: Timeline) -> Timeline:
        merged = Timeline()
        for tl in timelines:
            for step in tl.steps:
                merged.add_step(step)
        return merged

    def _apply_layout(self, kind: str, timeline: Timeline) -> Timeline:
        strategy = self._layout_map.get(kind, LayoutStrategy.LINEAR)
        engine: Optional[LayoutEngine] = None
        if strategy is LayoutStrategy.TREE:
            engine = self._tree_layout_engine
        elif strategy is LayoutStrategy.DAG:
            engine = self._dag_layout_engine
        else:
            engine = self._layout_engine

        if engine:
            offsets = self._structure_offsets
            # best-effort: inject offsets if engine exposes offset_* or setter
            if hasattr(engine, "set_offsets"):
                engine.set_offsets(offsets)
            if hasattr(engine, "set_structure_config"):
                engine.set_structure_config(self._structure_layout_config)
            else:
                # try common attribute names
                setattr(engine, "offset_map", offsets)
            return engine.apply_layout(timeline)
        return timeline

    # ------------------------------------------------------------------ #
    # Model registry + schema helpers
    # ------------------------------------------------------------------ #
    def _get_or_create_model(self, kind: str, structure_id: str) -> BaseModel:
        factory = MODEL_FACTORY_REGISTRY.get(kind)
        if factory is None:
            raise CommandError(f"No model registered for kind: {kind!r}")
        existing = self._structures.get(structure_id)
        if existing:
            return existing
        model = factory(structure_id)
        self._structures[structure_id] = model
        self._assign_offset(structure_id, kind)
        self._assign_layout_config(structure_id, kind)
        return model

    def _assign_offset(self, structure_id: str, kind: str) -> None:
        if structure_id in self._structure_offsets:
            return
        strategy = self._layout_map.get(kind, LayoutStrategy.LINEAR)
        row = self._row_index.get(strategy, 0)
        # baseline per strategy to reduce cross-kind overlap
        strategy_base_y = {
            LayoutStrategy.LINEAR: 0.0,
            LayoutStrategy.TREE: 400.0,
            LayoutStrategy.DAG: 800.0,
        }
        strategy_base_x = {
            LayoutStrategy.LINEAR: 0.0,
            LayoutStrategy.TREE: 0.0,
            LayoutStrategy.DAG: 200.0,
        }
        base_y = strategy_base_y.get(strategy, 0.0)
        base_x = strategy_base_x.get(strategy, 0.0)
        if strategy is LayoutStrategy.LINEAR:
            base_y += row * 220.0
        elif strategy is LayoutStrategy.TREE:
            base_y += row * 260.0
        elif strategy is LayoutStrategy.DAG:
            base_x += row * 260.0
        self._structure_offsets[structure_id] = (base_x, base_y)
        self._row_index[strategy] = row + 1

    def _assign_layout_config(self, structure_id: str, kind: str) -> None:
        cfg = self._kind_layout_config.get(kind, {})
        if cfg:
            self._structure_layout_config[structure_id] = cfg

    def _resolve_schema_and_op(
        self, command: Command
    ) -> Tuple[str, str, Mapping[str, Any]]:
        if not isinstance(command.payload, Mapping):
            raise CommandError("Command payload must be a mapping")
        
        payload = dict(command.payload)
        kind = payload.get("kind")

        if kind is None:
            # Try to resolve kind from existing structure
            model = self._structures.get(command.structure_id)
            if model:
                kind = model.kind
                payload["kind"] = kind
            elif command.type == CommandType.CREATE_STRUCTURE:
                # For CREATE_STRUCTURE, kind is mandatory if not existing
                raise CommandError("CREATE_STRUCTURE requires payload.kind")
            else:
                # Fallback to list for other commands if structure not found
                # (it will fail later with "Structure not found" anyway)
                kind = "list"
                payload["kind"] = kind

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
