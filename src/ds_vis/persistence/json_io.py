from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

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


def save_commands_to_file(commands: Sequence[Command], path: str | Path) -> None:
    """
    Serialize commands to JSON file. Raises CommandError on IO issues.
    """
    try:
        Path(path).write_text(commands_to_json(commands), encoding="utf-8")
    except OSError as exc:  # pragma: no cover - IO errors are environment specific
        raise CommandError(f"Failed to write commands to file: {exc}") from exc


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


def load_commands_from_file(path: str | Path) -> List[Command]:
    """
    Load and parse commands from a JSON file (list of dict).
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - IO errors are environment specific
        raise CommandError(f"Failed to read commands file: {exc}") from exc
    return commands_from_json(text)


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


# ------------------------------------------------------------------ #
# Scene Persistence (Snapshot-based)
# ------------------------------------------------------------------ #
def scene_to_json(scene_data: Mapping[str, object]) -> str:
    """
    Serialize scene state to JSON.
    """
    return json.dumps(scene_data, indent=2)


def save_scene_to_file(scene_data: Mapping[str, object], path: str | Path) -> None:
    """
    Save scene state to a JSON file.
    """
    try:
        Path(path).write_text(scene_to_json(scene_data), encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        raise CommandError(f"Failed to write scene to file: {exc}") from exc


def scene_from_json(text: str) -> Mapping[str, object]:
    """
    Deserialize scene state from JSON.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CommandError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, Mapping):
        raise CommandError("Scene JSON must be a mapping")
    return data


def load_scene_from_file(path: str | Path) -> Mapping[str, object]:
    """
    Load scene state from a JSON file.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover
        raise CommandError(f"Failed to read scene file: {exc}") from exc
    return scene_from_json(text)
