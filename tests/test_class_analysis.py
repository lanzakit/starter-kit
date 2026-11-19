from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def server():
    """Carga el servidor sin crear un cliente de red real."""
    with patch("anthropic.Anthropic"):
        return import_module("lanzakit_tester.server")


def test_analyze_recognizes_class_types_and_import_aliases(server, tmp_path):
    source = tmp_path / "models.py"
    source.write_text(
        """import dataclasses as dc
import pydantic as pd
from dataclasses import dataclass as record
from pydantic.v1 import BaseModel as LegacyModel
from example import BaseModel

class Plain(BaseModel):
    def save(self):
        pass

class Item(pd.BaseModel):
    count: int

class Derived(Item):
    pass

class Legacy(LegacyModel):
    pass

@dc.dataclass(frozen=True)
class Frozen:
    count: int

@record(frozen=False)
class Mutable:
    count: int

@record
class Defaults:
    count: int

class LegacyModel:
    pass

class Shadowed(LegacyModel):
    pass
""",
        encoding="utf-8",
    )

    result = server.analyze_python_file(str(source))
    assert {entry["name"]: entry["class_type"] for entry in result["classes"]} == {
        "Plain": "regular",
        "Item": "pydantic",
        "Derived": "pydantic",
        "Legacy": "pydantic",
        "Frozen": "dataclass_frozen",
        "Mutable": "dataclass",
        "Defaults": "dataclass",
        "LegacyModel": "regular",
        "Shadowed": "regular",
    }
    assert result["classes"][0]["methods"] == ["save"]
    assert result["classes"][0]["line"] == 7
    assert "pydantic" in result["imports"]


@pytest.mark.parametrize(
    ("source_text", "expected", "omitted"),
    [
        (
            "from pydantic import BaseModel\nclass Item(BaseModel):\n    count: int\n",
            ("Item", "Field()", "ValidationError"),
            ("FrozenInstanceError", "asdict()"),
        ),
        (
            "from dataclasses import dataclass\n@dataclass(frozen=True)\n"
            "class Item:\n    count: int\n",
            ("Item", "asdict()", "FrozenInstanceError"),
            ("ValidationError",),
        ),
        (
            "from dataclasses import dataclass\n@dataclass\nclass Item:\n    count: int\n",
            ("Item", "asdict()", "replace()"),
            ("FrozenInstanceError", "ValidationError"),
        ),
        (
            "class Item:\n    count: int\n",
            (),
            ("<contexto_clases>", "FrozenInstanceError", "ValidationError"),
        ),
    ],
)
def test_generated_prompt_uses_only_applicable_guidance(
    server, monkeypatch, tmp_path, source_text, expected, omitted
):
    source = tmp_path / "models.py"
    source.write_text(source_text, encoding="utf-8")
    response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="def test_item(): pass")],
        usage=SimpleNamespace(input_tokens=3, output_tokens=4),
    )
    create = Mock(return_value=response)
    monkeypatch.setattr(
        server,
        "anthropic_client",
        SimpleNamespace(messages=SimpleNamespace(create=create)),
    )

    assert (
        server.generate_tests_for_file(str(source))["test_code"]
        == response.content[0].text
    )
    create.assert_called_once()
    prompt = create.call_args.kwargs["messages"][0]["content"]
    if expected:
        assert "<contexto_clases>" in prompt
    for phrase in expected:
        assert phrase in prompt
    for phrase in omitted:
        assert phrase not in prompt
