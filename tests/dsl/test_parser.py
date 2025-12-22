import pytest

from ds_vis.core.exceptions import CommandError
from ds_vis.dsl.parser import parse_dsl


def test_parse_dsl_json_shortcut(create_cmd_factory):
    text = (
        '[{"structure_id": "s1", "type": "CREATE_STRUCTURE", '
        '"payload": {"kind": "list", "values": [1]}}]'
    )
    parsed = parse_dsl(text)
    assert len(parsed) == 1
    assert parsed[0].payload["values"] == [1]


def test_parse_dsl_invalid_json_raises():
    with pytest.raises(CommandError):
        parse_dsl("invalid")
