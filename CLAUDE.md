# Lanzakit Tester

Proyecto: MCP server en Python que genera y valida tests pytest con IA.

## Estado actual (noviembre 2026)

Paquete Python instalable (`pip install lanzakit-tester`), versión 0.1.0, aún sin publicar en PyPI.
Estructura `src/lanzakit_tester/` con build backend hatchling y CLI `lanzakit-tester`.

Producto funcional con 3 tools:
- `analyze_python_file`: analiza estructura del código con AST
- `generate_tests_for_file`: genera tests con Claude API
- `generate_and_validate_tests`: genera + valida sintaxis + ejecuta pytest

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
- Thinking desactivado para ahorrar tokens (reactivable cuando se quiera)

## Próximos pasos

- README público para GitHub
- Publicar en PyPI como `lanzakit-tester` (el empaquetado ya está listo)
- Landing en lanzakit.dev con waitlist
- Lanzamiento en X/LinkedIn + Product Hunt

## Contexto personal

Ingeniera full stack en Jalasoft (La Paz, Bolivia).
Prefiere respuestas concisas y directas.
Comunica en español.

## Reglas del proyecto

- Nunca commitear `.env`
- Tests en español (comentarios) pero nombres de funciones en inglés
- Mantener imports ordenados: stdlib → third party → local
- Modelo API siempre desde constante/config, nunca hardcoded en varias partes

## Pendientes conocidos

- Renombrar repo de `starter-kit` a `lanzakit-tester` antes del lanzamiento público
- Reservar handle @lanzakit en X/Twitter
- Crear archivos de badges reales cuando se publique en PyPI
