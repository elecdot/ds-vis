from __future__ import annotations

import argparse
import io
import sys
from typing import Optional

from ds_vis.core.exceptions import CommandError
from ds_vis.core.scene.scene_graph import SceneGraph
from ds_vis.dsl.parser import parse_dsl, run_commands


def _read_input(args: argparse.Namespace) -> str:
    if isinstance(args.text, str):
        return args.text
    if isinstance(args.file, io.TextIOBase):
        return args.file.read()
    return sys.stdin.read()


def run_cli(argv: Optional[list[str]] = None) -> int:
    """
    Minimal CLI hook: parse DSL/JSON text and apply to SceneGraph.

    This is intended as a developer hook; rendering is not invoked.
    """
    parser = argparse.ArgumentParser(description="Run DSL/JSON commands")
    parser.add_argument(
        "--file",
        type=argparse.FileType("r", encoding="utf-8"),
        help="Path to DSL/JSON command file (default: stdin)",
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Inline DSL/JSON string (overrides --file/stdin)",
    )
    args = parser.parse_args(argv)

    try:
        text = _read_input(args)
        commands = parse_dsl(text)
        sg = SceneGraph()
        run_commands(commands, sg)
        print(f"Executed {len(commands)} command(s)")
        return 0
    except CommandError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main() -> None:  # pragma: no cover - console entry
    sys.exit(run_cli())


if __name__ == "__main__":  # pragma: no cover
    main()
