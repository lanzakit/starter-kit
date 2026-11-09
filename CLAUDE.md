# Lanzakit Tester

Proyecto: MCP server en Python que genera y valida tests pytest con IA.

## Estado actual (noviembre 2026)

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

# Probar generación de tests
python -c "from lanzakit_server import generate_and_validate_tests; print(generate_and_validate_tests('/ruta/archivo.py')['summary'])"

# Correr tests manualmente
pytest test_hola_claude.py -v
```

## Arquitectura

- `lanzakit_server.py`: MCP server con las 3 tools
- `hola_claude.py`: script de ejemplo "hola mundo" con Claude API
- `.env`: contiene ANTHROPIC_API_KEY (nunca commitear)

## Decisiones tomadas

- Modelo: Claude Sonnet 5 (fijo por ahora)
- `max_tokens`: 16384 con thinking desactivado
- Prompt engineering con delimitadores XML
- `_clean_code_output()` remueve markdown fences
- `_run_pytest` usa `sys.executable -m pytest` para encontrar pytest desde cualquier contexto
- Thinking desactivado para ahorrar tokens (reactivable cuando se quiera)

## Próximos pasos

- README público para GitHub
- Empaquetar para PyPI como `lanzakit-tester`
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
