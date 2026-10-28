"""
Lanzakit Tester - MCP Server

Agente de IA para generar y analizar tests de Python.
Primera versión: solo analiza archivos Python básicos.
"""
from mcp.server.mcpserver import MCPServer
from pathlib import Path
import ast

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
            # Solo funciones del nivel superior (no métodos de clases)
            # Esta lógica simplificada se mejorará después
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


if __name__ == "__main__":
    # Correr el server usando stdio (lo que Claude Desktop espera)
    mcp.run(transport="stdio")