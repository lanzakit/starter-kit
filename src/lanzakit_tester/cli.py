"""Entrypoint de línea de comandos de Lanzakit Tester."""
import argparse

from lanzakit_tester import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lanzakit-tester",
        description="Lanzakit Tester: MCP server que genera y valida tests pytest con IA. "
        "Sin argumentos, arranca el servidor MCP por stdio.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.parse_args()

    # Import diferido: evita inicializar el servidor si solo se pide --help/--version
    from lanzakit_tester.server import run

    run()


if __name__ == "__main__":
    main()
