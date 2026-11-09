# Contribuir a Lanzakit Tester

¡Gracias por tu interés! Toda contribución es bienvenida: bugs, ideas, docs y código.

## Reportar un issue

1. Busca primero si ya existe un issue similar.
2. Abre uno nuevo e incluye:
   - Qué esperabas que pasara y qué pasó realmente.
   - Pasos para reproducirlo (idealmente con un archivo `.py` mínimo).
   - Versión de Python y sistema operativo.
   - Mensajes de error completos.

Nunca pegues tu `ANTHROPIC_API_KEY` ni el contenido de tu `.env`.

## Proponer una feature

Abre un issue describiendo el problema que quieres resolver y tu propuesta.
Conviene acordar el enfoque antes de escribir código, así evitamos trabajo perdido.

## Hacer un Pull Request

1. Haz fork del repositorio.
2. Crea una rama desde `main`: `git checkout -b feat/mi-cambio`
3. Haz tus cambios y commits pequeños y claros.
4. Verifica que los tests pasen: `pytest -v`
5. Haz push a tu fork y abre el PR explicando qué cambia y por qué.

Mensajes de commit sugeridos: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.

## Estilo de código

- Sigue [PEP 8](https://peps.python.org/pep-0008/).
- Formatea con [black](https://black.readthedocs.io/) y ordena imports con [isort](https://pycqa.github.io/isort/):

  ```bash
  black .
  isort .
  ```

- Orden de imports: stdlib → third party → local.

## Convenciones del proyecto

- Comentarios y docstrings en español; nombres de funciones y variables en inglés.
- El modelo de la API se define en una sola constante/config, nunca hardcoded en varios lugares.
- Nunca commitees `.env` ni credenciales.

## Licencia

Al contribuir aceptas que tu aporte se distribuya bajo la licencia [MIT](LICENSE) del proyecto.
