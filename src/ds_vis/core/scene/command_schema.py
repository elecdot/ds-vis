from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Mapping, Tuple, Type

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import CommandType

Validator = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class CommandSchema:
    required: Dict[str, Type[Any]] = field(default_factory=dict)
    optional: Dict[str, Tuple[Type[Any], ...]] = field(default_factory=dict)
    allow_extra: bool = False
    validators: Tuple[Validator, ...] = ()

    def validate(self, payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping):
            raise CommandError("Command payload must be a mapping")

        for key, expected_type in self.required.items():
            if key not in payload:
                raise CommandError(f"Missing required field: {key}")
            if not isinstance(payload.get(key), expected_type):
                raise CommandError(f"Field {key!r} must be {expected_type.__name__}")

        for key, expected_types in self.optional.items():
            if key in payload and payload.get(key) is not None:
                value = payload.get(key)
                if not isinstance(value, expected_types):
                    raise CommandError(
                        f"Field {key!r} must be a "
                        f"{self._type_names(expected_types)} when present"
                    )

        if not self.allow_extra:
            allowed = set(self.required) | set(self.optional)
            unknown = set(payload.keys()) - allowed
            if unknown:
                unknown_list = ", ".join(sorted(unknown))
                raise CommandError(f"Unexpected payload fields: {unknown_list}")

        for validator in self.validators:
            validator(payload)

    @staticmethod
    def _type_names(types: Tuple[Type[Any], ...]) -> str:
        names = [t.__name__ for t in types]
        return " or ".join(names)


def _require_index_or_value(context: str) -> Validator:
    def _validate(payload: Mapping[str, Any]) -> None:
        if payload.get("index") is None and payload.get("value") is None:
            raise CommandError(f"{context} requires index or value")

    return _validate


# (CommandType, kind) -> CommandSchema
SCHEMA_REGISTRY: Dict[Tuple[CommandType, str], CommandSchema] = {
    (CommandType.CREATE_STRUCTURE, "list"): CommandSchema(
        required={"kind": str},
        optional={"values": (list, tuple)},
    ),
    (CommandType.DELETE_STRUCTURE, "list"): CommandSchema(
        required={"kind": str},
    ),
    (CommandType.DELETE_NODE, "list"): CommandSchema(
        required={"kind": str, "index": int},
    ),
    (CommandType.INSERT, "list"): CommandSchema(
        required={"kind": str, "index": int, "value": object},
    ),
    (CommandType.SEARCH, "list"): CommandSchema(
        required={"kind": str},
        optional={"index": (int,), "value": (object,)},
        validators=(_require_index_or_value("SEARCH"),),
    ),
    (CommandType.UPDATE, "list"): CommandSchema(
        required={"kind": str, "new_value": object},
        optional={"index": (int,), "value": (object,)},
        validators=(_require_index_or_value("UPDATE"),),
    ),
}


# (CommandType, kind) -> model operation name
MODEL_OP_REGISTRY: Dict[Tuple[CommandType, str], str] = {
    (CommandType.CREATE_STRUCTURE, "list"): "create",
    (CommandType.DELETE_STRUCTURE, "list"): "delete_all",
    (CommandType.DELETE_NODE, "list"): "delete_index",
    (CommandType.INSERT, "list"): "insert",
    (CommandType.SEARCH, "list"): "search",
    (CommandType.UPDATE, "list"): "update",
}
