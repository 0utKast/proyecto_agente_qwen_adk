"""
run_bridge.py — Punto de entrada del servidor de integración WhatsApp ↔ ADK.

Uso:
    # Desde la raíz del proyecto (con el venv activado):
    python -m whatsapp_bridge.run_bridge

    # O directamente:
    python whatsapp_bridge/run_bridge.py
"""

import uvicorn
from .config import bridge_settings


def main():
    print("\n" + "=" * 60)
    print("  🤖 WhatsApp Bridge — ADK/Qwen3 × Twilio Sandbox")
    print("=" * 60)
    print(f"  Servidor: http://{bridge_settings.BRIDGE_HOST}:{bridge_settings.BRIDGE_PORT}")
    print(f"  Webhook:  POST /webhook")
    print(f"  Health:   GET  /health")
    print()
    print("  ⚡ Pasos para habilitar el canal WhatsApp:")
    print("  1. En otra terminal: ngrok http 8001")
    print("  2. Copia la URL HTTPS de ngrok (ej: https://xxxx.ngrok-free.app)")
    print("  3. En Twilio Console > Sandbox > 'When a message comes in':")
    print("     pega la URL + /webhook  (método: POST)")
    print("  4. Envía un mensaje al número sandbox de Twilio desde WhatsApp")
    print("=" * 60 + "\n")

    uvicorn.run(
        "whatsapp_bridge.server:app",
        host=bridge_settings.BRIDGE_HOST,
        port=bridge_settings.BRIDGE_PORT,
        reload=False,   # reload=True causa problemas con asyncio + Ollama
        log_level="info",
    )


if __name__ == "__main__":
    main()
