from ds_vis.core.scene.command import CommandType
from ds_vis.llm.adapter import LLMAdapter, LLMClient


def test_adapter_parses_json_without_client() -> None:
    adapter = LLMAdapter()
    commands = adapter.to_commands(
        """[
            {"structure_id": "list-1", "type": "CREATE_STRUCTURE",
             "payload": {"kind": "list"}},
            {"structure_id": "list-1", "type": "DELETE_STRUCTURE",
             "payload": {"kind": "list"}}
        ]"""
    )
    assert [cmd.type for cmd in commands] == [
        CommandType.CREATE_STRUCTURE,
        CommandType.DELETE_STRUCTURE,
    ]


class DummyClient(LLMClient):
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.received: list[str] = []

    def generate(self, prompt: str) -> str:
        self.received.append(prompt)
        return self.reply


def test_adapter_uses_client_and_prefix() -> None:
    reply = """[
        {"structure_id": "list-2", "type": "INSERT",
         "payload": {"kind": "list", "index": 0, "value": 1}}
    ]"""
    client = DummyClient(reply=reply)
    adapter = LLMAdapter(client=client, prompt_prefix="translate: ")

    commands = adapter.to_commands("insert head 1 into list-2")

    assert client.received == ["translate: insert head 1 into list-2"]
    assert len(commands) == 1
    assert commands[0].type == CommandType.INSERT
    assert commands[0].payload["index"] == 0
