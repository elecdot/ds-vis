from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, runtime_checkable

from ds_vis.core.scene.command import Command
from ds_vis.dsl.parser import parse_dsl


@runtime_checkable
class LLMClient(Protocol):
    """
    Minimal client interface for LLM providers.

    Implementations should return a DSL string (or JSON fallback) that can be
    parsed into Commands.
    """

    def generate(self, prompt: str) -> str:
        ...


@dataclass
class LLMAdapter:
    """
    Bridge natural-language requests to Commands via DSL text.

    Current placeholder behavior:
    - If `client` is None, treat the incoming request as already-valid DSL/JSON.
    - Otherwise, delegate to the LLM client, then parse the returned DSL text.
    """

    client: Optional[LLMClient] = None
    prompt_prefix: str = ""

    def _build_prompt(self, request: str) -> str:
        if not self.prompt_prefix:
            return request
        return f"{self.prompt_prefix}{request}"

    def to_dsl(self, request: str) -> str:
        if self.client is None:
            return request
        prompt = self._build_prompt(request)
        return self.client.generate(prompt)

    def to_commands(self, request: str) -> List[Command]:
        dsl_text = self.to_dsl(request)
        return parse_dsl(dsl_text)
