from __future__ import annotations

import json
from typing import Iterable, List, Mapping

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.core.scene.command_schema import SCHEMA_REGISTRY


def commands_to_json(commands: Iterable[Command]) -> str:
    """
    Serialize a list of Commands to JSON (list of dict).
    """
    return json.dumps(
        [
            {
                "structure_id": cmd.structure_id,
                "type": cmd.type.name,
                "payload": cmd.payload,
            }
            for cmd in commands
        ]
    )


def commands_from_json(text: str) -> List[Command]:
    """
    Deserialize Commands from JSON and validate via SCHEMA_REGISTRY.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CommandError(f"Invalid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise CommandError("Command JSON must be a list")

    commands: List[Command] = []
    for item in data:
        if not isinstance(item, Mapping):
            raise CommandError("Each command must be a mapping")
        structure_id = item.get("structure_id")
        type_name = item.get("type")
        payload_raw = item.get("payload")
        if not isinstance(payload_raw, Mapping):
            raise CommandError("Command payload must be a mapping")
        payload: Mapping[str, object] = payload_raw
        if not isinstance(structure_id, str):
            raise CommandError("Command requires structure_id as string")
        if not isinstance(type_name, str):
            raise CommandError("Command requires type as string")
        try:
            cmd_type = CommandType[type_name]
        except KeyError as exc:
            raise CommandError(f"Unsupported command type: {type_name!r}") from exc
        _validate_command_payload(cmd_type, payload)
        commands.append(
            Command(structure_id=structure_id, type=cmd_type, payload=payload)
        )
    return commands


def _validate_command_payload(
    cmd_type: CommandType, payload: Mapping[str, object]
) -> None:
    if not isinstance(payload, Mapping):
        raise CommandError("Command payload must be a mapping")
    kind = payload.get("kind")
    if not isinstance(kind, str):
        raise CommandError("Command requires payload.kind as string")
    schema = SCHEMA_REGISTRY.get((cmd_type, kind))
    if schema is None:
        raise CommandError(f"Unsupported command/kind combination: {kind!r}")
    schema.validate(payload)
