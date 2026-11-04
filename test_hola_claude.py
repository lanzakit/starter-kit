# Tests para hola_claude.py
# Nota: el módulo bajo prueba instancia Anthropic() y llama os.getenv()
# a nivel de import, por lo que se debe mockear ANTES de importar.
import os
from unittest.mock import MagicMock, patch
 
import pytest
 
 
@pytest.fixture
def mock_env_api_key(monkeypatch):
    """Simula la variable de entorno ANTHROPIC_API_KEY para evitar depender del entorno real."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-test-key")
 
 
@pytest.fixture
def hola_claude_module(mock_env_api_key):
    """
    Importa el módulo bajo prueba con el cliente Anthropic mockeado,
    evitando llamadas reales de red al instanciar el cliente en el import.
    """
    with patch("anthropic.Anthropic") as mock_anthropic_cls:
        mock_client_instance = MagicMock()
        mock_anthropic_cls.return_value = mock_client_instance
 
        import importlib
        import hola_claude
 
        importlib.reload(hola_claude)
 
        yield hola_claude, mock_client_instance
 
        # Limpieza: remover del cache de módulos para no afectar otros tests
        import sys
        sys.modules.pop("hola_claude", None)
 
 
def _build_fake_message(text="Hola Raquel, listo para ayudar.", input_tokens=10, output_tokens=5):
    """Construye una respuesta falsa con la misma forma que el objeto Message de Anthropic."""
    fake_message = MagicMock()
    fake_content_block = MagicMock()
    fake_content_block.text = text
    fake_message.content = [fake_content_block]
    fake_message.usage.input_tokens = input_tokens
    fake_message.usage.output_tokens = output_tokens
    return fake_message
 
 
def test_saludar_llama_a_messages_create_con_modelo_correcto(hola_claude_module):
    """Protege contra regresiones que cambien accidentalmente el modelo usado en la llamada a la API."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message()
 
    module.saludar()
 
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["model"] == "claude-sonnet-5"
 
 
def test_saludar_llama_a_messages_create_con_max_tokens_correcto(hola_claude_module):
    """Protege contra cambios no intencionales en el límite de tokens de salida configurado."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message()
 
    module.saludar()
 
    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["max_tokens"] == 512
 
 
def test_saludar_envia_mensaje_con_rol_user(hola_claude_module):
    """Protege contra errores en la estructura del mensaje enviado (rol incorrecto rompería la API real)."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message()
 
    module.saludar()
 
    _, kwargs = mock_client.messages.create.call_args
    messages = kwargs["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
 
 
def test_saludar_contenido_del_mensaje_menciona_lanzakit_tester(hola_claude_module):
    """Verifica que el contenido del prompt no se corrompa ni pierda el contexto del proyecto."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message()
 
    module.saludar()
 
    _, kwargs = mock_client.messages.create.call_args
    content = kwargs["messages"][0]["content"]
    assert "Lanzakit Tester" in content
    assert "Raquel" in content
 
 
def test_saludar_imprime_respuesta_de_claude(hola_claude_module, capsys):
    """Detecta regresiones donde el texto de respuesta deje de imprimirse en consola."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message(
        text="Sí, estoy listo para ayudarte."
    )
 
    module.saludar()
 
    captured = capsys.readouterr()
    assert "Sí, estoy listo para ayudarte." in captured.out
 
 
def test_saludar_imprime_conteo_de_tokens_input_y_output(hola_claude_module, capsys):
    """Detecta regresiones en el formato o cálculo del resumen de tokens usados."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message(
        input_tokens=42, output_tokens=17
    )
 
    module.saludar()
 
    captured = capsys.readouterr()
    assert "42 input" in captured.out
    assert "17 output" in captured.out
 
 
def test_saludar_no_llama_a_create_mas_de_una_vez(hola_claude_module):
    """Protege contra regresiones que dupliquen llamadas a la API (costo extra innecesario)."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.return_value = _build_fake_message()
 
    module.saludar()
 
    assert mock_client.messages.create.call_count == 1
 
 
def test_saludar_propaga_excepcion_si_falla_la_llamada_a_la_api(hola_claude_module):
    """Verifica que errores de la API no sean silenciados, permitiendo diagnosticar fallos reales."""
    module, mock_client = hola_claude_module
    mock_client.messages.create.side_effect = ConnectionError("fallo de red simulado")
 
    with pytest.raises(ConnectionError, match="fallo de red simulado"):
        module.saludar()
 


