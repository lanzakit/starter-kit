# Lanzakit Tester

Proyecto: MCP server en Python que genera y valida tests pytest con IA.

## Estado actual (noviembre 2026)

Paquete Python instalable (`pip install lanzakit-tester`).
- v0.1.0: publicada en PyPI.
- v0.2.0: en desarrollo en la rama `feat/v0.2-coverage` (cobertura con pytest-cov + protecciones de seguridad, cierra el issue #1).
- Landing live en lanzakit.dev.
Estructura `src/lanzakit_tester/` con build backend hatchling y CLI `lanzakit-tester`.

Producto funcional con 3 tools:
- `analyze_python_file`: analiza estructura del código con AST
- `generate_tests_for_file`: genera tests con Claude API
- `generate_and_validate_tests`: genera + valida sintaxis + ejecuta pytest + mide cobertura (v0.2)

Loop end-to-end funciona. 8 tests generados y 8 passed en pruebas reales.

## Stack técnico

- Python 3.14
- MCP SDK v2 (`from mcp.server.mcpserver import MCPServer`)
- Claude API (modelo: `claude-sonnet-5`)
- pytest para validación
- uv como gestor de paquetes
- venv en `.venv/`

## Comandos clave

```bash
# Activar entorno
source .venv/bin/activate

# Instalar en modo editable (con deps de desarrollo)
uv pip install -e ".[dev]"

# Verificar CLI
lanzakit-tester --version

# Probar generación de tests
python -c "from lanzakit_tester import generate_and_validate_tests; print(generate_and_validate_tests('/ruta/archivo.py')['summary'])"

# Correr tests manualmente
pytest examples -v
```

## Arquitectura

- `pyproject.toml`: fuente de verdad de metadata y dependencias (hatchling)
- `src/lanzakit_tester/server.py`: MCP server con las 3 tools, constante `MODEL`, `run()`
- `src/lanzakit_tester/cli.py`: entrypoint argparse (`--version`; sin args arranca MCP por stdio)
- `src/lanzakit_tester/__init__.py`: expone las 3 tools y `__version__`
- `examples/`: `hola_claude.py` (hola mundo con Claude API) y su test; no son parte del paquete
- `.env`: contiene ANTHROPIC_API_KEY (nunca commitear)

## Decisiones tomadas

- Modelo: Claude Sonnet 5 (fijo por ahora), definido como constante `MODEL` en `src/lanzakit_tester/server.py`
- Versión única en `pyproject.toml`; se lee con `importlib.metadata` y se pasa a `MCPServer(version=...)`
- `max_tokens`: 16384 con thinking desactivado
- Prompt engineering con delimitadores XML
- `_clean_code_output()` remueve markdown fences
- `_run_pytest` usa `sys.executable -m pytest` para encontrar pytest desde cualquier contexto
- Seguridad (v0.2): pytest corre con `_safe_env()` (sin variables sensibles), `save_to` solo acepta `test_*.py` y no sobrescribe sin `overwrite=True`
- Thinking desactivado para ahorrar tokens (reactivable cuando se quiera)

## Próximos pasos

- Terminar y mergear v0.2.0 (cobertura + seguridad) y publicarla en PyPI
- Lanzamiento en X/LinkedIn + Product Hunt

## Deuda técnica menor

No se resuelve antes del lanzamiento (perfeccionismo mata lanzamientos):

- `requirements-dev.txt` es redundante con `pip install -e ".[dev]"`
- `CONTRIBUTING.md` no menciona `pip install -e ".[dev]"`

## Reglas del proyecto

- Nunca commitear `.env`
- Tests en español (comentarios) pero nombres de funciones en inglés
- Mantener imports ordenados: stdlib → third party → local
- Modelo API siempre desde constante/config, nunca hardcoded en varias partes

## Pendientes conocidos

- Renombrar repo de `starter-kit` a `lanzakit-tester` antes del lanzamiento público
- Reservar handle @lanzakit en X/Twitter
