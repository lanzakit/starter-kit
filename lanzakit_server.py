"""
Lanzakit Tester - MCP Server

Agente de IA para generar y analizar tests de Python.
"""
import ast
import os
import subprocess
import tempfile
from pathlib import Path
import sys

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

@mcp.tool()
def generate_and_validate_tests(
    file_path: str,
    save_to: str = ""
) -> dict:
    """
    Flujo completo: genera tests, valida sintaxis, ejecuta y reporta.
    
    Esta tool cierra el loop de calidad: no solo genera tests sino que
    verifica que compilen y que pasen antes de entregárselos al usuario.
    
    Args:
        file_path: Ruta absoluta al archivo .py a testear
        save_to: Ruta donde guardar el archivo de tests (opcional).
                 Si está vacío, usa test_<nombre>.py al lado del archivo original.
    
    Returns:
        Dict con:
        - test_code: código de los tests generados
        - saved_to: dónde se guardó
        - syntax_valid: bool
        - execution: resultados de pytest (passed/failed/errors)
        - summary: resumen legible
    """
    path = Path(file_path)
    
    # Paso 1: generar los tests (reutilizamos la tool existente)
    generation_result = generate_tests_for_file(file_path)
    
    if "error" in generation_result:
        return generation_result
    
    test_code = generation_result["test_code"]
    
    # Paso 2: validar sintaxis
    syntax_check = _validate_syntax(test_code)
    
    if not syntax_check["valid"]:
        return {
            "test_code": test_code,
            "saved_to": None,
            "syntax_valid": False,
            "syntax_error": syntax_check["error"],
            "execution": None,
            "summary": f"❌ Tests generados pero con error de sintaxis: {syntax_check['error']}",
            "tokens_used": generation_result["tokens_used"],
        }
    
    # Paso 3: determinar dónde guardar
    if save_to:
        save_path = Path(save_to)
    else:
        save_path = path.parent / f"test_{path.stem}.py"
    
    # Paso 4: guardar el archivo
    try:
        save_path.write_text(test_code, encoding="utf-8")
    except Exception as e:
        return {
            "test_code": test_code,
            "saved_to": None,
            "syntax_valid": True,
            "execution": None,
            "summary": f"⚠️ Tests válidos pero no se pudieron guardar: {e}",
            "tokens_used": generation_result["tokens_used"],
        }
    
    # Paso 5: ejecutar pytest
    execution = _run_pytest(save_path, source_dir=path.parent)
    
    # Paso 6: armar resumen
    if execution.get("all_passed"):
        summary = (
            f"✅ {execution['passed']} tests generados y pasaron. "
            f"Guardado en: {save_path}"
        )
    elif "error" in execution:
        summary = f"⚠️ Tests generados pero no se pudieron ejecutar: {execution['error']}"
    else:
        summary = (
            f"⚠️ {execution.get('passed', 0)} pasaron, "
            f"{execution.get('failed', 0)} fallaron, "
            f"{execution.get('errors', 0)} errores. "
            f"Guardado en: {save_path}"
        )
    
    return {
        "test_code": test_code,
        "saved_to": str(save_path),
        "syntax_valid": True,
        "execution": execution,
        "summary": summary,
        "tokens_used": generation_result["tokens_used"],
    }

def _validate_syntax(code: str) -> dict:
    """Valida que el código sea Python sintácticamente correcto."""
    try:
        ast.parse(code)
        return {"valid": True}
    except SyntaxError as e:
        return {
            "valid": False,
            "error": f"Línea {e.lineno}: {e.msg}",
            "offset": e.offset,
        }


def _run_pytest(test_file_path: Path, source_dir: Path, timeout: int = 30) -> dict:
    """
    Ejecuta pytest sobre un archivo de tests en un subproceso aislado.
    
    Args:
        test_file_path: Ruta al archivo de tests
        source_dir: Directorio desde donde ejecutar pytest (para resolución de imports)
        timeout: Segundos máximos antes de matar el proceso
    
    Returns:
        Dict con: passed, failed, errors, output, stderr
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file_path), "-v", "--tb=short", "--no-header"],
            cwd=str(source_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        output = result.stdout
        stderr = result.stderr
        
        # Parsear resultados básicos del output
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        errors = output.count(" ERROR")
        
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "all_passed": result.returncode == 0,
            "output": output[-2000:],
            "stderr": stderr[-500:] if stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {
            "error": f"pytest excedió timeout de {timeout}s",
            "all_passed": False,
        }
    except FileNotFoundError:
        return {
            "error": "pytest no está instalado en el entorno",
            "all_passed": False,
        }
    except Exception as e:
        return {
            "error": f"Error ejecutando pytest: {e}",
            "all_passed": False,
        }

if __name__ == "__main__":
    # Correr el server usando stdio (lo que Claude Desktop espera)
    mcp.run(transport="stdio")