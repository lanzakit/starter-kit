"""
Tests para hola_claude.py: verifica la lógica de saludar()
mockeando la frontera externa (API de Anthropic).
"""
import os
from unittest.mock import MagicMock, patch

import pytest


# El módulo bajo prueba instancia Anthropic() al importarse (nivel módulo).
# Por eso mockeamos la clase Anthropic ANTES de importar hola_claude,
# para evitar llamadas reales o errores por falta de API key.
@pytest.fixture
def mock_anthropic_client():
    """Reemplaza la clase Anthropic por un mock antes de importar el módulo."""
    with patch("anthropic.Anthropic") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class, mock_instance


@pytest.fixture
def hola_claude_module(mock_anthropic_client, monkeypatch):
    """Importa (o recarga) hola_claude con Anthropic ya mockeado."""
    # Aseguramos que exista una API key dummy para que os.getenv no sea None.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-tests")

    import importlib
    import sys

    # Si el módulo ya fue importado por otro test, lo removemos para
    # forzar una reimportación limpia con el mock activo.
    if "hola_claude" in sys.modules:
        del sys.modules["hola_claude"]

    module = importlib.import_module("hola_claude")
    importlib.reload(module)
    return module


def _build_fake_message(text="Respuesta de prueba", input_tokens=10, output_tokens=5):
    """Construye un objeto mensaje falso con la forma que espera el código."""
    fake_message = MagicMock()
    fake_content_block = MagicMock()
    fake_content_block.text = text
    fake_message.content = [fake_content_block]
    fake_message.usage.input_tokens = input_tokens
    fake_message.usage.output_tokens = output_tokens
    return fake_message


def test_saludar_llama_a_messages_create_con_modelo_correcto(
    hola_claude_module, mock_anthropic_client
):
    """Protege contra regresiones que cambien el modelo o rompan la llamada a la API."""
    _, mock_instance = mock_anthropic_client
    mock_instance.messages.create.return_value = _build_fake_message()

    hola_claude_module.client = mock_instance  # aseguramos el mock en el módulo
    hola_claude_module.saludar()

    mock_instance.messages.create.assert_called_once()
    _, kwargs = mock_instance.messages.create.call_args
    assert kwargs["model"] == "claude-sonnet-5"
    assert kwargs["max_tokens"] == 512


def test_saludar_envia_mensaje_con_rol_user_y_contenido_no_vacio(
    hola_claude_module, mock_anthropic_client
):
    """Protege contra cambios accidentales en el payload enviado a Claude."""
    _, mock_instance = mock_anthropic_client
    mock_instance.messages.create.return_value = _build_fake_message()

    hola_claude_module.client = mock_instance
    hola_claude_module.saludar()

    _, kwargs = mock_instance.messages.create.call_args
    messages = kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert isinstance(messages[0]["content"], str)
    assert len(messages[0]["content"]) > 0


def test_saludar_imprime_respuesta_y_tokens(
    hola_claude_module, mock_anthropic_client, capsys
):
    """Protege contra regresiones en el formato de salida: texto y conteo de tokens."""
    _, mock_instance = mock_anthropic_client
    mock_instance.messages.create.return_value = _build_fake_message(
        text="Sí, estoy listo.", input_tokens=42, output_tokens=7
    )

    hola_claude_module.client = mock_instance
    hola_claude_module.saludar()

    captured = capsys.readouterr()
    assert "Sí, estoy listo." in captured.out
    assert "42 input" in captured.out
    assert "7 output" in captured.out


@pytest.mark.parametrize(
    "input_tokens,output_tokens",
    [
        (0, 0),  # caso límite: respuesta sin consumo de tokens reportado
        (1, 1),  # caso mínimo no nulo
        (100000, 50000),  # caso de valores grandes, detecta overflow o truncamiento
    ],
)
def test_saludar_formatea_distintos_valores_de_tokens(
    hola_claude_module, mock_anthropic_client, capsys, input_tokens, output_tokens
):
    """Protege contra errores de formato al construir el string de tokens usados."""
    _, mock_instance = mock_anthropic_client
    mock_instance.messages.create.return_value = _build_fake_message(
        input_tokens=input_tokens, output_tokens=output_tokens
    )

    hola_claude_module.client = mock_instance
    hola_claude_module.saludar()

    captured = capsys.readouterr()
    assert f"{input_tokens} input" in captured.out
    assert f"{output_tokens} output" in captured.out


def test_saludar_propaga_excepcion_si_api_falla(
    hola_claude_module, mock_anthropic_client
):
    """Verifica que un error de la API no se silencia, sino que se propaga al llamador."""
    _, mock_instance = mock_anthropic_client
    mock_instance.messages.create.side_effect = RuntimeError("fallo de red simulado")

    hola_claude_module.client = mock_instance

    with pytest.raises(RuntimeError, match="fallo de red simulado"):
        hola_claude_module.saludar()


def test_client_se_inicializa_con_api_key_desde_entorno(
    mock_anthropic_client, monkeypatch
):
    """Protege contra regresiones donde la API key deje de leerse de la variable de entorno."""
    mock_class, _ = mock_anthropic_client
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-especifica-de-test")

    import importlib
    import sys

    if "hola_claude" in sys.modules:
        del sys.modules["hola_claude"]
    importlib.import_module("hola_claude")

    mock_class.assert_called_once_with(api_key="clave-especifica-de-test")