from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, Mapping, Tuple, Type

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import CommandType

Validator = Callable[[Mapping[str, Any]], None]
if TYPE_CHECKING:  # pragma: no cover - typing only
    from ds_vis.core.models import BaseModel


@dataclass(frozen=True)
class CommandSchema:
    required: Dict[str, Type[Any]] = field(default_factory=dict)
    optional: Dict[str, Tuple[Type[Any], ...]] = field(default_factory=dict)
    allow_extra: bool = False
    validators: Tuple[Validator, ...] = ()

    def validate(self, payload: Mapping[str, Any]) -> None:
        _ensure_mapping(payload)

        _validate_required_fields(payload, self.required)
        _validate_optional_fields(payload, self.optional)
        _validate_no_extra_fields(
            payload,
            allowed=set(self.required) | set(self.optional),
            allow_extra=self.allow_extra,
        )
        _run_validators(payload, self.validators)


def _ensure_mapping(payload: Mapping[str, Any]) -> None:
    if not isinstance(payload, Mapping):
        raise CommandError("Command payload must be a mapping")


def _validate_required_fields(
    payload: Mapping[str, Any], required: Dict[str, Type[Any]]
) -> None:
    for key, expected_type in required.items():
        if key not in payload:
            raise CommandError(f"Missing required field: {key}")
        if not isinstance(payload.get(key), expected_type):
            raise CommandError(
                f"Field {key!r} must be {_type_names((expected_type,))}"
            )


def _validate_optional_fields(
    payload: Mapping[str, Any], optional: Dict[str, Tuple[Type[Any], ...]]
) -> None:
    for key, expected_types in optional.items():
        if key in payload and payload.get(key) is not None:
            value = payload.get(key)
            if not isinstance(value, expected_types):
                msg = _type_names(expected_types)
                raise CommandError(f"Field {key!r} must be a {msg} when present")


def _validate_no_extra_fields(
    payload: Mapping[str, Any], allowed: set[str], allow_extra: bool
) -> None:
    if allow_extra:
        return
    unknown = set(payload.keys()) - allowed
    if unknown:
        unknown_list = ", ".join(sorted(unknown))
        raise CommandError(f"Unexpected payload fields: {unknown_list}")


def _run_validators(
    payload: Mapping[str, Any], validators: Tuple[Validator, ...]
) -> None:
    for validator in validators:
        validator(payload)


def _type_names(types: Tuple[Type[Any], ...]) -> str:
    names = [t.__name__ for t in types]
    return " or ".join(names)


def _require_index_or_value(context: str) -> Validator:
    def _validate(payload: Mapping[str, Any]) -> None:
        if payload.get("index") is None and payload.get("value") is None:
            raise CommandError(f"{context} requires index or value")

    return _validate


# (CommandType, kind) -> CommandSchema
SCHEMA_REGISTRY: Dict[Tuple[CommandType, str], CommandSchema] = {}

# (CommandType, kind) -> model operation name
MODEL_OP_REGISTRY: Dict[Tuple[CommandType, str], str] = {}

# kind -> model factory
MODEL_FACTORY_REGISTRY: Dict[str, Callable[[str], "BaseModel"]] = {}


def register_command(
    cmd_type: CommandType, kind: str, schema: CommandSchema, model_op: str
) -> None:
    """
    Register a command schema and its mapping to a model operation.

    Usage for new structures:
        register_command(CommandType.CREATE_STRUCTURE, "tree", tree_schema, "create")
    """
    SCHEMA_REGISTRY[(cmd_type, kind)] = schema
    MODEL_OP_REGISTRY[(cmd_type, kind)] = model_op


def register_model_factory(kind: str, factory: Callable[[str], "BaseModel"]) -> None:
    """
    Register a model factory for a structure kind.

    Usage:
        register_model_factory("tree", lambda sid: TreeModel(structure_id=sid))
    """
    MODEL_FACTORY_REGISTRY[kind] = factory


def _register_defaults() -> None:
    from ds_vis.core.models import BstModel, ListModel
    from ds_vis.core.models.seqlist import SeqlistModel
    from ds_vis.core.models.stack import StackModel

    register_command(
        CommandType.CREATE_STRUCTURE,
        "list",
        CommandSchema(required={"kind": str}, optional={"values": (list, tuple)}),
        "create",
    )
    register_command(
        CommandType.DELETE_STRUCTURE,
        "list",
        CommandSchema(required={"kind": str}),
        "delete_all",
    )
    register_command(
        CommandType.DELETE_NODE,
        "list",
        CommandSchema(required={"kind": str, "index": int}),
        "delete_index",
    )
    register_command(
        CommandType.INSERT,
        "list",
        CommandSchema(required={"kind": str, "index": int, "value": object}),
        "insert",
    )
    register_command(
        CommandType.SEARCH,
        "list",
        CommandSchema(
            required={"kind": str},
            optional={"index": (int,), "value": (object,)},
            validators=(_require_index_or_value("SEARCH"),),
        ),
        "search",
    )
    register_command(
        CommandType.UPDATE,
        "list",
        CommandSchema(
            required={"kind": str, "new_value": object},
            optional={"index": (int,), "value": (object,)},
            validators=(_require_index_or_value("UPDATE"),),
        ),
        "update",
    )
    register_model_factory(
        "list", lambda structure_id: ListModel(structure_id=structure_id)
    )
    register_command(
        CommandType.CREATE_STRUCTURE,
        "stack",
        CommandSchema(required={"kind": str}, optional={"values": (list, tuple)}),
        "create",
    )
    register_command(
        CommandType.DELETE_STRUCTURE,
        "stack",
        CommandSchema(required={"kind": str}),
        "delete_all",
    )
    register_command(
        CommandType.DELETE_NODE,
        "stack",
        CommandSchema(
            required={"kind": str},
            optional={"index": (int,)},
        ),
        "pop",
    )
    register_command(
        CommandType.INSERT,
        "stack",
        CommandSchema(
            required={"kind": str, "value": object},
            optional={"index": (int,)},
        ),
        "push",
    )
    register_command(
        CommandType.SEARCH,
        "stack",
        CommandSchema(required={"kind": str, "value": object}),
        "search",
    )
    register_model_factory(
        "stack", lambda structure_id: StackModel(structure_id=structure_id)
    )
    register_command(
        CommandType.CREATE_STRUCTURE,
        "seqlist",
        CommandSchema(required={"kind": str}, optional={"values": (list, tuple)}),
        "create",
    )
    register_command(
        CommandType.DELETE_STRUCTURE,
        "seqlist",
        CommandSchema(required={"kind": str}),
        "delete_all",
    )
    register_command(
        CommandType.DELETE_NODE,
        "seqlist",
        CommandSchema(required={"kind": str, "index": int}),
        "delete_index",
    )
    register_command(
        CommandType.INSERT,
        "seqlist",
        CommandSchema(required={"kind": str, "index": int, "value": object}),
        "insert",
    )
    register_command(
        CommandType.SEARCH,
        "seqlist",
        CommandSchema(
            required={"kind": str},
            optional={"index": (int,), "value": (object,)},
            validators=(_require_index_or_value("SEARCH"),),
        ),
        "search",
    )
    register_command(
        CommandType.UPDATE,
        "seqlist",
        CommandSchema(
            required={"kind": str, "new_value": object},
            optional={"index": (int,), "value": (object,)},
            validators=(_require_index_or_value("UPDATE"),),
        ),
        "update",
    )
    register_model_factory(
        "seqlist", lambda structure_id: SeqlistModel(structure_id=structure_id)
    )
    register_command(
        CommandType.CREATE_STRUCTURE,
        "bst",
        CommandSchema(required={"kind": str}, optional={"values": (list, tuple)}),
        "create",
    )
    register_command(
        CommandType.INSERT,
        "bst",
        CommandSchema(required={"kind": str, "value": object}),
        "insert",
    )
    register_command(
        CommandType.DELETE_STRUCTURE,
        "bst",
        CommandSchema(required={"kind": str}),
        "delete_all",
    )
    register_command(
        CommandType.SEARCH,
        "bst",
        CommandSchema(required={"kind": str, "value": object}),
        "search",
    )
    register_command(
        CommandType.DELETE_NODE,
        "bst",
        CommandSchema(required={"kind": str, "value": object}),
        "delete_value",
    )
    register_model_factory(
        "bst", lambda structure_id: BstModel(structure_id=structure_id)
    )


_register_defaults()
