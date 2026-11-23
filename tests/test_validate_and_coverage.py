"""Tests de v0.2: cobertura con pytest-cov y protecciones de seguridad."""

from importlib import import_module
from unittest.mock import patch

import pytest


@pytest.fixture
def server():
    """Carga el servidor sin crear un cliente de red real."""
    with patch("anthropic.Anthropic"):
        return import_module("lanzakit_tester.server")


SOURCE = """def clasificar(n):
    if n < 0:
        return "negativo"
    return "positivo"
"""

# Test que solo prueba una rama: la cobertura NO debe ser 100%
PARTIAL_TESTS = """from calc import clasificar


def test_positivo():
    assert clasificar(5) == "positivo"
"""


def _fake_generation(test_code):
    return {
        "file": "calc.py",
        "test_code": test_code,
        "tokens_used": {"input": 1, "output": 1},
    }


def test_reports_coverage_and_missing_lines(server, tmp_path):
    source = tmp_path / "calc.py"
    source.write_text(SOURCE, encoding="utf-8")

    with patch.object(
        server, "generate_tests_for_file", return_value=_fake_generation(PARTIAL_TESTS)
    ):
        result = server.generate_and_validate_tests(str(source))

    assert result["execution"]["all_passed"] is True
    assert result["coverage"] is not None
    assert 0 < result["coverage"]["percent"] < 100
    assert (
        3 in result["coverage"]["missing_lines"]
    )  # return "negativo" nunca se ejecutó
    assert "📊 Cobertura" in result["summary"]


def test_does_not_overwrite_existing_tests(server, tmp_path):
    source = tmp_path / "calc.py"
    source.write_text(SOURCE, encoding="utf-8")
    existing = tmp_path / "test_calc.py"
    existing.write_text("# tests escritos a mano\n", encoding="utf-8")

    with patch.object(server, "generate_tests_for_file") as generate:
        result = server.generate_and_validate_tests(str(source))

    assert "error" in result
    assert existing.read_text(encoding="utf-8") == "# tests escritos a mano\n"
    generate.assert_not_called()  # no se gastan tokens si no se puede guardar


@pytest.mark.parametrize("bad_name", [".bashrc", "calc.py", "test_calc.txt", ".env"])
def test_rejects_save_to_outside_test_files(server, tmp_path, bad_name):
    source = tmp_path / "calc.py"
    source.write_text(SOURCE, encoding="utf-8")

    with patch.object(server, "generate_tests_for_file") as generate:
        result = server.generate_and_validate_tests(
            str(source), save_to=str(tmp_path / bad_name)
        )

    assert "error" in result
    assert not (tmp_path / bad_name).exists() or bad_name == "calc.py"
    generate.assert_not_called()


def test_generated_tests_cannot_read_api_key(server, tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-falsa-para-test")
    monkeypatch.setenv("GITHUB_TOKEN", "ghp-falso")
    source = tmp_path / "calc.py"
    source.write_text(SOURCE, encoding="utf-8")
    spy_tests = """import os


def test_env_is_clean():
    assert "ANTHROPIC_API_KEY" not in os.environ
    assert "GITHUB_TOKEN" not in os.environ
"""

    with patch.object(
        server, "generate_tests_for_file", return_value=_fake_generation(spy_tests)
    ):
        result = server.generate_and_validate_tests(str(source))

    assert result["execution"]["all_passed"] is True, result["execution"]["output"]


def test_works_without_pytest_cov(server, tmp_path):
    source = tmp_path / "calc.py"
    source.write_text(SOURCE, encoding="utf-8")

    with (
        patch.object(server, "_coverage_available", return_value=False),
        patch.object(
            server,
            "generate_tests_for_file",
            return_value=_fake_generation(PARTIAL_TESTS),
        ),
    ):
        result = server.generate_and_validate_tests(str(source))

    assert result["execution"]["all_passed"] is True
    assert result["coverage"] is None
    assert "Cobertura" not in result["summary"]


def test_generated_tests_cannot_read_urls_with_credentials(
    server, tmp_path, monkeypatch
):
    # Variable con nombre inocente pero con clave dentro de la URL
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
    # URL sin credenciales: debe seguir pasando
    monkeypatch.setenv("PUBLIC_URL", "https://lanzakit.dev/docs")
    source = tmp_path / "calc.py"
    source.write_text(SOURCE, encoding="utf-8")
    spy_tests = """import os


def test_env_is_clean():
    assert "DATABASE_URL" not in os.environ
    assert os.environ.get("PUBLIC_URL") == "https://lanzakit.dev/docs"
    assert "PATH" in os.environ
"""

    with patch.object(
        server, "generate_tests_for_file", return_value=_fake_generation(spy_tests)
    ):
        result = server.generate_and_validate_tests(str(source))

    assert result["execution"]["all_passed"] is True, result["execution"]["output"]


def test_safe_env_keeps_normal_variables(server, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost/db")
    env = server._safe_env()

    assert "DATABASE_URL" not in env
    assert "PATH" in env
