"""
twilio_client.py — Wrapper sobre el SDK oficial de Twilio para enviar mensajes de WhatsApp.

Uso:
    from whatsapp_bridge.twilio_client import twilio_client
    await twilio_client.send_text("whatsapp:+34600123456", "Hola desde el agente!")
"""

import logging
from twilio.rest import Client

from .config import bridge_settings

logger = logging.getLogger(__name__)


class TwilioWhatsAppClient:
    """
    Cliente asíncrono (wrapper) para el SDK de Twilio.
    El SDK de Twilio es síncrono, lo ejecutamos en un thread executor
    para no bloquear el event loop de FastAPI.
    """

    def __init__(self):
        self._client: Client | None = None

    def _get_client(self) -> Client:
        """Lazy initialization del cliente Twilio."""
        if self._client is None:
            if not bridge_settings.validate_credentials():
                raise RuntimeError(
                    "Credenciales Twilio no configuradas. "
                    "Asegúrate de definir TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en el .env"
                )
            self._client = Client(
                bridge_settings.TWILIO_ACCOUNT_SID,
                bridge_settings.TWILIO_AUTH_TOKEN
            )
        return self._client

    def send_text_sync(self, to: str, body: str) -> str:
        """
        Envía un mensaje de texto de WhatsApp de forma síncrona.

        Args:
            to:   Número destino con prefijo whatsapp:, ej: whatsapp:+34600123456
            body: Texto del mensaje (máx ~1600 chars; Twilio lo divide automáticamente)

        Returns:
            SID del mensaje enviado.
        """
        client = self._get_client()

        # Twilio limita a ~1600 caracteres por mensaje. Truncamos con aviso.
        MAX_LEN = 1500
        if len(body) > MAX_LEN:
            body = body[:MAX_LEN] + "\n\n[Respuesta truncada. Continúa enviando 'más' para el resto.]"

        message = client.messages.create(
            from_=bridge_settings.TWILIO_WHATSAPP_NUMBER,
            to=to,
            body=body
        )
        logger.info(f"[Twilio] Mensaje enviado a {to} — SID: {message.sid}")
        return message.sid

    async def send_text(self, to: str, body: str) -> str:
        """
        Versión asíncrona de send_text_sync.
        Ejecuta el SDK síncrono en el thread pool para no bloquear FastAPI.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        sid = await loop.run_in_executor(None, self.send_text_sync, to, body)
        return sid


# Instancia global reutilizable
twilio_client = TwilioWhatsAppClient()
