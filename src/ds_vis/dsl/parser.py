from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, List, Mapping

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.command import Command, CommandType
from ds_vis.persistence.json_io import commands_from_json

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ds_vis.core.scene.scene_graph import SceneGraph

KEYWORDS = {"list", "seqlist", "stack", "bst", "git", "huffman"}


def parse_dsl(text: str, existing_kinds: Mapping[str, str] | None = None) -> List[Command]:
    """
    Minimal DSL parser (v0.2):
      - Accept JSON array of commands (兼容旧版)
      - Accept simple文本语法，语句以 ';' 分隔，格式：
        <kind> <id> [= [values...]] | <op> <id> [args...]
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
    # Normalize existing_kinds to lowercase keys for robust lookup
    ctx: dict[str, str] = {k.lower(): v for k, v in (existing_kinds or {}).items()}
    
    # 1. Strip comments
    processed_lines = []
    for line in text.splitlines():
        comment_idx = -1
        in_q = False
        for idx, char in enumerate(line):
            if char == '"':
                in_q = not in_q
            elif char == '#' and not in_q:
                comment_idx = idx
                break
        if comment_idx != -1:
            line = line[:comment_idx]
        processed_lines.append(line)
    text = "\n".join(processed_lines)

    # 2. Split into statements by ';' or newline (respecting brackets)
    raw_statements: List[str] = []
    current: List[str] = []
    in_bracket = False
    in_quote = False
    for char in text:
        if char == '"':
            in_quote = not in_quote
            current.append(char)
        elif in_quote:
            current.append(char)
        elif char == '[':
            in_bracket = True
            current.append(char)
        elif char == ']':
            in_bracket = False
            current.append(char)
        elif (char == ';' or char == '\n') and not in_bracket:
            stmt = "".join(current).strip()
            if stmt:
                raw_statements.append(stmt)
            current = []
        else:
            current.append(char)
    
    final_stmt = "".join(current).strip()
    if final_stmt:
        raw_statements.append(final_stmt)

    for stmt in raw_statements:
        cmd, kind = _parse_statement(stmt, ctx)
        if kind:
            ctx[cmd.structure_id.lower()] = kind
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
    first_token_lower = tokens[0].lower()
    if first_token_lower in KEYWORDS and len(tokens) >= 2:
        cmd = _parse_create(tokens)
        return cmd, first_token_lower

    op = first_token_lower
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
    """
    Robust tokenizer for DSL:
      - Splits by whitespace.
      - Treats '=' as a separate token even if attached to other chars (e.g., 'id=[1,2]').
      - Keeps '[...]' as a single token even if it contains spaces.
      - Respects double quotes for strings.
    """
    tokens: List[str] = []
    current: List[str] = []
    in_quote = False
    in_bracket = False
    
    i = 0
    while i < len(stmt):
        ch = stmt[i]
        
        if ch == '"':
            in_quote = not in_quote
            i += 1
            continue
            
        if in_quote:
            current.append(ch)
            i += 1
            continue
            
        if ch == '[':
            in_bracket = True
            current.append(ch)
        elif ch == ']':
            in_bracket = False
            current.append(ch)
        elif ch.isspace() and not in_bracket:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(ch)
        i += 1
        
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
    # Handle 'id=[1,2]' or 'id = [1,2]' or 'id=[1, 2]'
    if "=" in tokens[1]:
        structure_id, val_part = tokens[1].split("=", 1)
        if not val_part and len(tokens) >= 3:
            val_part = tokens[2]
        values = _parse_values_literal(val_part)
    else:
        structure_id = tokens[1]
        values = []
        if len(tokens) >= 3:
            if tokens[2] == "=":
                if len(tokens) >= 4:
                    values = _parse_values_literal(tokens[3])
            elif tokens[2].startswith("="):
                values = _parse_values_literal(tokens[2][1:])
    
    payload: Mapping[str, object] = {"kind": kind}
    if values:
        payload = {"kind": kind, "values": values}
    return Command(structure_id, CommandType.CREATE_STRUCTURE, payload)


def _parse_insert(tokens: List[str], ctx: Mapping[str, str]) -> Command:
    if len(tokens) < 3:
        raise CommandError("insert requires id and value")
    structure_id = tokens[1]
    value = _coerce_value(tokens[-1])
    kind = _kind_from_ctx(structure_id, ctx)
    payload: dict[str, object] = {"value": value}
    if kind:
        payload["kind"] = kind
    if len(tokens) == 4:
        payload["index"] = _coerce_value(tokens[2])
    return Command(structure_id, CommandType.INSERT, payload)


def _parse_delete(tokens: List[str], ctx: Mapping[str, str]) -> Command:
    if len(tokens) < 2:
        raise CommandError("delete requires id")
    structure_id = tokens[1]
    kind = _kind_from_ctx(structure_id, ctx)
    payload: dict[str, object] = {}
    if kind:
        payload["kind"] = kind
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
    payload: dict[str, object] = {}
    if kind:
        payload["kind"] = kind
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
    kind = _kind_from_ctx(structure_id, ctx)
    payload: dict[str, object] = {"new_value": new_value}
    if kind:
        payload["kind"] = kind
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


def _kind_from_ctx(structure_id: str, ctx: Mapping[str, str]) -> str | None:
    # ctx keys are already normalized to lowercase in parse_dsl
    return ctx.get(structure_id.lower())
