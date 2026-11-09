# Lanzakit Tester

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![License MIT](https://img.shields.io/badge/license-MIT-green)

**Tests de pytest generados por IA, y verificados antes de que los veas.**

Lanzakit Tester es un MCP server que lee tu código Python, genera tests con Claude y los ejecuta para confirmar que compilan y pasan. Dejas de revisar tests que ni siquiera corren.

## Features

- 🧪 **Generación de tests con Claude**: analiza tu código y produce tests pytest listos para usar.
- ✅ **Validación automática**: verifica la sintaxis y ejecuta pytest antes de entregarte el resultado.
- 🔌 **MCP nativo**: funciona con Claude Desktop y cualquier cliente compatible con MCP.
- 🌳 **Análisis con AST**: entiende funciones, clases y firmas antes de armar el prompt.
- 🇪🇸 **Español-first**: comentarios de los tests y documentación en español.
- 🔓 **Open source**: licencia MIT, sin lock-in.

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Una API key de Anthropic (`ANTHROPIC_API_KEY`)
- Acceso al modelo `claude-sonnet-5`

## Instalación

Primero clona el repo y prepara el entorno (ambas opciones lo necesitan):

```bash
git clone https://github.com/lanzakit/starter-kit.git
cd starter-kit
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=tu_api_key" > .env
```

> El archivo `.env` contiene tu API key. Nunca lo subas a git.

### Opción A: Vía Claude Desktop (MCP config)

Agrega el server a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lanzakit-tester": {
      "command": "/ruta/a/starter-kit/.venv/bin/python",
      "args": ["/ruta/a/starter-kit/lanzakit_server.py"]
    }
  }
}
```

Reinicia Claude Desktop y las 3 tools aparecerán disponibles.

### Opción B: Vía CLI con uv

Sin cliente MCP, puedes invocar las tools directamente desde Python:

```bash
uv run python -c "from lanzakit_server import generate_and_validate_tests; print(generate_and_validate_tests('/ruta/a/tu_archivo.py')['summary'])"
```

## Uso

Tienes un archivo `hola_claude.py` (el "hola mundo" del proyecto, versión simplificada):

```python
import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def saludar():
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=512,
        messages=[{"role": "user", "content": "Hola Claude"}]
    )
    print(message.content[0].text)
```

Desde Claude Desktop, pídele:

> Genera y valida tests para `/ruta/a/hola_claude.py`

Claude llama a la tool `generate_and_validate_tests` y obtienes un resumen como este:

```text
✅ 8 tests generados y pasaron. Guardado en: /ruta/a/test_hola_claude.py
```

El archivo `test_hola_claude.py` queda junto a tu código, listo para correr con `pytest`.

### Tools disponibles

| Tool | Qué hace |
|------|----------|
| `analyze_python_file` | Analiza la estructura del código con AST. |
| `generate_tests_for_file` | Genera tests pytest con Claude. |
| `generate_and_validate_tests` | Genera, valida sintaxis, guarda y ejecuta pytest. |

## Cómo funciona

```text
código .py
   │
   ▼
análisis AST  ──►  prompt a Claude  ──►  tests generados
                                              │
                                              ▼
                      resultado  ◄──  ejecución pytest  ◄──  validación sintáctica
```

1. Lee tu archivo y extrae su estructura con AST.
2. Arma un prompt con el código y su contexto, y se lo envía a Claude (`claude-sonnet-5`).
3. Limpia la respuesta (por ejemplo, quita markdown fences).
4. Valida que los tests tengan sintaxis Python correcta.
5. Guarda el archivo y ejecuta pytest.
6. Devuelve un resumen: cuántos pasaron, fallaron o dieron error.

## Roadmap

- [x] 3 tools funcionales
- [x] Validación end-to-end
- [ ] Distribución vía PyPI
- [ ] Landing en lanzakit.dev
- [ ] Soporte para más frameworks de testing

## Contribuir

¿Encontraste un bug o tienes una idea? Abre un [issue](https://github.com/lanzakit/starter-kit/issues) o envía un PR. Lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer el flujo de trabajo.

## Licencia

Distribuido bajo licencia MIT. Consulta el archivo [LICENSE](LICENSE).

---

[@lanzakit](https://x.com/lanzakit) · Construido en Bolivia 🇧🇴 para devs hispanohablantes
