"""
Lanzakit Tester - MCP Server

Agente de IA para generar y analizar tests de Python.
"""
import ast
import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

load_dotenv()
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def _clean_code_output(text: str) -> str:
    """Remueve markdown fences si Claude los agrega a pesar del prompt."""
    text = text.strip()
    if text.startswith("```python"):
        text = text[9:].lstrip()
    elif text.startswith("```"):
        text = text[3:].lstrip()
    if text.endswith("```"):
        text = text[:-3].rstrip()
    return text


# Crear el servidor MCP
mcp = MCPServer("lanzakit-tester")


@mcp.tool()
def analyze_python_file(file_path: str) -> dict:
    """
    Analiza un archivo Python y devuelve información estructural.

    Lee el archivo, lo parsea con AST (Abstract Syntax Tree) y extrae:
    - Nombre del archivo
    - Número de líneas totales
    - Lista de clases definidas
    - Lista de funciones definidas (incluye métodos de clases)
    - Imports utilizados

    Args:
        file_path: Ruta absoluta al archivo .py a analizar

    Returns:
        Diccionario con el análisis estructural del archivo
    """
    path = Path(file_path)

    # Validaciones básicas
    if not path.exists():
        return {"error": f"El archivo {file_path} no existe"}

    if path.suffix != ".py":
        return {"error": f"El archivo debe ser .py, no {path.suffix}"}

    # Leer el contenido
    try:
        source_code = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"No se pudo leer el archivo: {e}"}

    # Parsear con AST
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return {"error": f"El archivo tiene errores de sintaxis: {e}"}

    # Extraer información
    classes = []
    functions = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "methods": [
                    n.name for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "args": [arg.arg for arg in node.args.args]
            })
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    return {
        "file": path.name,
        "total_lines": len(source_code.splitlines()),
        "classes": classes,
        "functions": functions,
        "imports": imports,
    }


GENERATE_TESTS_PROMPT = """Eres Lanzakit Tester, un ingeniero senior de Python especializado en pytest.

Tu tarea: generar un archivo de tests pytest de alta calidad para el código proporcionado. Los tests deben detectar regresiones reales, ser deterministas y enseñar buenas prácticas con comentarios breves en español neutro LATAM.

<codigo_a_testear ruta="{file_path}">
{source_code}
</codigo_a_testear>

<reglas_fundamentales>

1. FIDELIDAD AL CÓDIGO
- Testea el comportamiento OBSERVABLE del código, no lo que crees que debería hacer
- No inventes contratos ni validaciones que el código no implementa
- Usa docstrings, type hints y validaciones como fuente de verdad

2. EDGE CASES JUSTIFICADOS
- Cada test debe responder: "¿qué regresión específica detectaría?"
- Deriva casos de las ramas, operaciones y límites reales del código
- No incluyas casos genéricos sin justificación

3. IMPORTS Y DEPENDENCIAS
- Solo usa: pytest, unittest.mock, biblioteca estándar
- NO inventes: fixtures custom, pytest-plugins externos, módulos que no existen
- Para importar el código bajo prueba usa el nombre del archivo sin extensión
- Si no puedes determinar la ruta de import con confianza, NO inventes

4. PYTEST MODERNO
- Usa pytest.mark.parametrize cuando varios casos compartan verificación
- Usa pytest.raises para excepciones
- Usa fixtures solo cuando reduzcan duplicación real
- Nombres: test_<funcion>_<escenario>_<resultado>

5. COMENTARIOS EDUCATIVOS
- Comentarios BREVES en español explicando qué regresión protege cada test
- Un comentario por test o por grupo parametrizado, no por línea
- Nombres de funciones y variables en inglés (convención Python estándar)

6. MOCKING RESPONSABLE
- No mockees la función bajo prueba
- Mockea solo fronteras externas (red, archivos, servicios)
- Prefiere lógica real sin mocks cuando sea posible

</reglas_fundamentales>

<prohibiciones>
- NO inventar imports, fixtures, módulos o dependencias
- NO usar assert True ni aserciones triviales
- NO capturar Exception genérica para hacer pasar un test
- NO incluir Markdown, ```python, preámbulos ni explicaciones externas al código
- NO modificar el código fuente del usuario
</prohibiciones>

<formato_salida>
Devuelve EXCLUSIVAMENTE código Python válido, listo para guardar como test_<nombre>.py.
Primera línea: un import o un comentario Python.
No incluyas nada antes ni después del código.
</formato_salida>"""


@mcp.tool()
def generate_tests_for_file(file_path: str) -> dict:
    """
    Genera tests pytest de alta calidad para un archivo Python usando Claude.

    Lee el archivo, lo envía a Claude con un prompt optimizado para testing,
    y devuelve el código de los tests generado.

    Args:
        file_path: Ruta absoluta al archivo .py a testear

    Returns:
        Diccionario con:
        - file: nombre del archivo original
        - test_code: código Python de los tests generados
        - tokens_used: cuántos tokens consumió la llamada
    """
    path = Path(file_path)

    if not path.exists():
        return {"error": f"El archivo {file_path} no existe"}

    if path.suffix != ".py":
        return {"error": f"El archivo debe ser .py, no {path.suffix}"}

    try:
        source_code = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"No se pudo leer el archivo: {e}"}

    if not source_code.strip():
        return {"error": "El archivo está vacío"}

    # Llamar a Claude
    try:
        message = anthropic_client.messages.create(
            model="claude-sonnet-5",
            max_tokens=16384,
            thinking={"type": "disabled"},
            messages=[
                {
                    "role": "user",
                    "content": GENERATE_TESTS_PROMPT.format(
                        source_code=source_code,
                        file_path=str(path)
                    )
                }
            ]
        )
    except Exception as e:
        return {"error": f"Error llamando a Claude API: {e}"}

    # Buscar el primer bloque de texto (puede haber ThinkingBlocks antes)
    test_code = next(
        (block.text for block in message.content if block.type == "text"),
        None
    )

    if test_code is None:
        return {"error": "Claude no devolvió contenido de texto"}

    # Limpiar markdown fences si los hay
    test_code = _clean_code_output(test_code)

    return {
        "file": path.name,
        "test_code": test_code,
        "tokens_used": {
            "input": message.usage.input_tokens,
            "output": message.usage.output_tokens
        }
    }


if __name__ == "__main__":
    # Correr el server usando stdio (lo que Claude Desktop espera)
    mcp.run(transport="stdio")