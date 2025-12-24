from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Mapping

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.persistence.json_io import commands_from_json

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ds_vis.core.scene.scene_graph import SceneGraph

KEYWORDS = {"list", "seqlist", "stack", "bst", "git", "huffman"}


def parse_dsl(text: str) -> List[Command]:
    """
    Minimal DSL parser (v0.2):
      - Accept JSON array of commands (兼容旧版)
      - Accept simple文本语法，语句以 ';' 分隔，格式：
        <kind> <id> [= [values...]] | <op> <id> [args...]
      - 支持操作：
         create: `list L1 = [1,2,3]` 或 `bst B1 = [5,3,7]`
         insert: `insert L1 1 5`
         delete: `delete L1 0` (index) / `delete B1 val=5`
         search: `search L1 val=5` / `search B1 7`
         update: `update L1 1 9`
         push/pop: `push S1 3`, `pop S1`
         commit: `commit G1 "msg"`
         checkout: `checkout G1 main`
         init git: `git G1 init`
    """
    text = text.strip()
    if not text:
        return []

    # JSON branch for compatibility
    if text.lstrip().startswith("["):
        try:
            return commands_from_json(text)
        except Exception as exc:  # pragma: no cover - defensive
            raise CommandError(f"Failed to parse DSL input: {exc}") from exc

    commands: List[Command] = []
    ctx: dict[str, str] = {}  # structure_id -> kind
    for raw_stmt in text.split(";"):
        stmt = raw_stmt.strip()
        if not stmt:
            continue
        cmd, kind = _parse_statement(stmt, ctx)
        if kind:
            ctx[cmd.structure_id] = kind
        commands.append(cmd)
    return commands


def run_commands(commands: Iterable[Command], scene_graph: "SceneGraph") -> None:
    """
    Helper to apply a sequence of commands to a SceneGraph.
    """
    for cmd in commands:
        scene_graph.apply_command(cmd)


# --------------------------------------------------------------------------- #
# Internal parsing helpers
# --------------------------------------------------------------------------- #
def _parse_statement(stmt: str, ctx: Mapping[str, str]) -> tuple[Command, str | None]:
    """
    stmt grammar (minimal, whitespace separated):
      create: <kind> <id> = [csv]
      insert: insert <id> <index?> <value?>
      delete: delete <id> <index?> | delete <id> val=<value>
      search: search <id> <index?> | search <id> val=<value>
      update: update <id> <index> <new_value>
      push/pop: push <id> <value> | pop <id>
      git: git <id> init | commit <id> <msg> | checkout <id> <target>
    """
    tokens = _tokenize(stmt)
    if not tokens:
        raise CommandError("Empty statement")

    # create with assignment: kind id = [1,2,3]
    if tokens[0] in KEYWORDS and len(tokens) >= 2:
        cmd = _parse_create(tokens)
        return cmd, tokens[0]

    op = tokens[0].lower()
    if op == "insert":
        return _parse_insert(tokens, ctx), None
    if op == "delete":
        return _parse_delete(tokens, ctx), None
    if op == "search":
        return _parse_search(tokens, ctx), None
    if op == "update":
        return _parse_update(tokens, ctx), None
    if op == "push":
        return _parse_push(tokens), None
    if op == "pop":
        return _parse_pop(tokens), None
    if op == "commit":
        return _parse_commit(tokens), None
    if op == "checkout":
        return _parse_checkout(tokens), None
    if op == "git":
        cmd, kind = _parse_git(tokens)
        return cmd, kind

    raise CommandError(f"Unsupported statement: {stmt!r}")


def _tokenize(stmt: str) -> List[str]:
    # simple split respecting quoted strings
    tokens: List[str] = []
    current: List[str] = []
    in_quote = False
    for ch in stmt:
        if ch == '"':
            in_quote = not in_quote
            continue
        if ch.isspace() and not in_quote:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current))
    return tokens


def _parse_values_literal(lit: str) -> List[object]:
    if not lit.startswith("[") or not lit.endswith("]"):
        raise CommandError("Values literal must be [comma separated]")
    body = lit[1:-1].strip()
    if not body:
        return []
    parts = [p.strip() for p in body.split(",") if p.strip()]
    return [_coerce_value(p) for p in parts]


def _coerce_value(raw: str) -> object:
    if raw.lstrip("-").isdigit():
        try:
            return int(raw)
        except ValueError:
            return raw
    try:
        return float(raw)
    except ValueError:
        return raw


def _parse_create(tokens: List[str]) -> Command:
    kind = tokens[0]
    structure_id = tokens[1]
    values: List[object] = []
    if len(tokens) >= 4 and tokens[2] == "=":
        values = _parse_values_literal(tokens[3])
    payload: Mapping[str, object] = {"kind": kind}
    if values:
        payload = {"kind": kind, "values": values}
    return Command(structure_id, CommandType.CREATE_STRUCTURE, payload)


def _parse_insert(tokens: List[str], ctx: Mapping[str, str]) -> Command:
    if len(tokens) < 3:
        raise CommandError("insert requires id and value")
    structure_id = tokens[1]
    value = _coerce_value(tokens[-1])
    payload: dict[str, object] = {
        "kind": _kind_from_ctx(structure_id, ctx),
        "value": value,
    }
    if len(tokens) == 4:
        payload["index"] = _coerce_value(tokens[2])
    return Command(structure_id, CommandType.INSERT, payload)


def _parse_delete(tokens: List[str], ctx: Mapping[str, str]) -> Command:
    if len(tokens) < 2:
        raise CommandError("delete requires id")
    structure_id = tokens[1]
    kind = _kind_from_ctx(structure_id, ctx)
    payload: dict[str, object] = {"kind": kind}
    if len(tokens) >= 3:
        if tokens[2].startswith("val="):
            payload["value"] = _coerce_value(tokens[2].split("=", 1)[1])
        else:
            if kind == "bst":
                payload["value"] = _coerce_value(tokens[2])
            else:
                payload["index"] = _coerce_value(tokens[2])
    return Command(structure_id, CommandType.DELETE_NODE, payload)


def _parse_search(tokens: List[str], ctx: Mapping[str, str]) -> Command:
    if len(tokens) < 2:
        raise CommandError("search requires id")
    structure_id = tokens[1]
    kind = _kind_from_ctx(structure_id, ctx)
    payload: dict[str, object] = {"kind": kind}
    if len(tokens) >= 3:
        if tokens[2].startswith("val="):
            payload["value"] = _coerce_value(tokens[2].split("=", 1)[1])
        else:
            if kind == "bst":
                payload["value"] = _coerce_value(tokens[2])
            else:
                payload["index"] = _coerce_value(tokens[2])
    return Command(structure_id, CommandType.SEARCH, payload)


def _parse_update(tokens: List[str], ctx: Mapping[str, str]) -> Command:
    if len(tokens) < 4:
        raise CommandError("update requires id, index/value, new_value")
    structure_id = tokens[1]
    new_value = _coerce_value(tokens[-1])
    payload: dict[str, object] = {
        "kind": _kind_from_ctx(structure_id, ctx),
        "new_value": new_value,
    }
    if tokens[2].startswith("val="):
        payload["value"] = _coerce_value(tokens[2].split("=", 1)[1])
    else:
        payload["index"] = _coerce_value(tokens[2])
    return Command(structure_id, CommandType.UPDATE, payload)


def _parse_push(tokens: List[str]) -> Command:
    if len(tokens) < 3:
        raise CommandError("push requires id and value")
    structure_id = tokens[1]
    value = _coerce_value(tokens[2])
    return Command(
        structure_id,
        CommandType.INSERT,
        payload={"kind": "stack", "value": value, "index": 0},
    )


def _parse_pop(tokens: List[str]) -> Command:
    if len(tokens) < 2:
        raise CommandError("pop requires id")
    structure_id = tokens[1]
    return Command(structure_id, CommandType.DELETE_NODE, payload={"kind": "stack"})


def _parse_commit(tokens: List[str]) -> Command:
    if len(tokens) < 2:
        raise CommandError("commit requires id")
    structure_id = tokens[1]
    message = tokens[2] if len(tokens) >= 3 else "commit"
    return Command(
        structure_id,
        CommandType.INSERT,
        payload={"kind": "git", "message": message},
    )


def _parse_checkout(tokens: List[str]) -> Command:
    if len(tokens) < 3:
        raise CommandError("checkout requires id and target")
    structure_id = tokens[1]
    target = tokens[2]
    return Command(
        structure_id,
        CommandType.SEARCH,
        payload={"kind": "git", "target": target},
    )


def _parse_git(tokens: List[str]) -> tuple[Command, str | None]:
    if len(tokens) < 3:
        raise CommandError("git statement requires id and subcommand")
    structure_id = tokens[1]
    sub = tokens[2].lower()
    if sub == "init":
        return (
            Command(structure_id, CommandType.CREATE_STRUCTURE, {"kind": "git"}),
            "git",
        )
    if sub == "commit":
        msg = tokens[3] if len(tokens) >= 4 else "commit"
        return (
            Command(
                structure_id,
                CommandType.INSERT,
                payload={"kind": "git", "message": msg},
            ),
            None,
        )
    if sub == "checkout":
        if len(tokens) < 4:
            raise CommandError("git checkout requires target")
        target = tokens[3]
        return (
            Command(
                structure_id,
                CommandType.SEARCH,
                payload={"kind": "git", "target": target},
            ),
            None,
        )
    raise CommandError(f"Unsupported git subcommand: {sub}")


def _kind_from_ctx(structure_id: str, ctx: Mapping[str, str]) -> str:
    return ctx.get(structure_id, "list")
