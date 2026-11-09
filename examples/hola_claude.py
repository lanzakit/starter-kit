"""
Primer script: saludar a Claude y verificar que la API funciona.
Este script es el 'Hola Mundo' del proyecto Lanzakit Tester.
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Inicializar cliente de Claude
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def saludar():
    """Envía un mensaje de prueba a Claude y muestra la respuesta."""
    message = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": (
                    "Hola Claude, soy Raquel y estoy construyendo "
                    "Lanzakit Tester, un agente de IA para generar tests "
                    "de Python. ¿Estás listo para ayudarme en este proyecto? "
                    "Responde en 2 líneas."
                ),
            }
        ],
    )

    print("Respuesta de Claude:")
    print("-" * 50)
    print(message.content[0].text)
    print("-" * 50)
    print(
        f"\nTokens usados: "
        f"{message.usage.input_tokens} input + "
        f"{message.usage.output_tokens} output"
    )


if __name__ == "__main__":
    saludar()