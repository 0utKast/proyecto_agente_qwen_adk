"""
config.py — Configuración del módulo whatsapp_bridge.

Variables de entorno necesarias (añadir al .env):
    TWILIO_ACCOUNT_SID   — SID de tu cuenta Twilio (empieza por AC...)
    TWILIO_AUTH_TOKEN    — Auth Token de tu cuenta Twilio
    TWILIO_WHATSAPP_NUMBER — Número Twilio del sandbox, ej: whatsapp:+14155238886
    BRIDGE_PORT          — Puerto del servidor FastAPI (default: 8001)
    ALLOWED_PHONE_NUMBERS — Números autorizados separados por comas (vacío = todos)
                            Ej: whatsapp:+34600000001,whatsapp:+34600000002
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class BridgeSettings(BaseSettings):
    # ── Twilio ──────────────────────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"  # Número sandbox por defecto

    # ── Servidor bridge ─────────────────────────────────────────────────────
    BRIDGE_HOST: str = "0.0.0.0"
    BRIDGE_PORT: int = 8001

    # ── Seguridad ───────────────────────────────────────────────────────────
    # Lista de números autorizados (con prefijo whatsapp:). Vacío = todos.
    # Ejemplo: "whatsapp:+34600123456,whatsapp:+34600654321"
    ALLOWED_PHONE_NUMBERS: str = ""

    # ── Agente ADK ──────────────────────────────────────────────────────────
    # Perfil del agente que responderá en WhatsApp
    WHATSAPP_AGENT_PROFILE: str = "arquitecto"

    class Config:
        # Carga el .env de la raíz del proyecto (dos niveles arriba de este archivo)
        env_file = str(Path(__file__).resolve().parent.parent / ".env")
        extra = "ignore"

    @property
    def allowed_numbers_set(self) -> set:
        """Devuelve el set de números autorizados, o set vacío si no hay restricción."""
        if not self.ALLOWED_PHONE_NUMBERS.strip():
            return set()
        return {n.strip() for n in self.ALLOWED_PHONE_NUMBERS.split(",") if n.strip()}

    def validate_credentials(self) -> bool:
        """Comprueba que las credenciales Twilio están configuradas."""
        return bool(self.TWILIO_ACCOUNT_SID and self.TWILIO_AUTH_TOKEN)


bridge_settings = BridgeSettings()
