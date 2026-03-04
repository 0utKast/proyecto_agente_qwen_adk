"""
session_manager.py — Gestión de sesiones ADK por número de teléfono.

Cada número de WhatsApp que envíe un mensaje obtiene su propia sesión ADK
aislada, con su propio historial de conversación. Esto permite que el agente
mantenga contexto entre mensajes del mismo usuario.
"""

import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


class WhatsAppSessionManager:
    """
    Mantiene un mapeo de número de teléfono → session_id del agente ADK.

    El session_id se usa en LocalADKAgent.run(session_id=...) para recuperar
    el historial de conversación de la memoria SQLite del agente.

    Uso:
        manager = WhatsAppSessionManager()
        session_id = manager.get_or_create(phone="whatsapp:+34600123456")
    """

    def __init__(self):
        # Dict: phone_number (str) → {"session_id": str, "created_at": datetime, "message_count": int}
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _normalize_phone(self, phone: str) -> str:
        """Elimina el prefijo 'whatsapp:' y espacios para usar como clave limpia."""
        return phone.strip().replace("whatsapp:", "").replace("+", "").replace(" ", "")

    def get_or_create(self, phone: str) -> str:
        """
        Devuelve el session_id asociado al número de teléfono.
        Si no existe, crea uno nuevo.

        Args:
            phone: Número con prefijo whatsapp:, ej: whatsapp:+34600123456

        Returns:
            session_id: Cadena utilizable en LocalADKAgent.run(session_id=...)
        """
        normalized = self._normalize_phone(phone)

        with self._lock:
            if normalized not in self._sessions:
                # Creamos un session_id descriptivo: wa_<número>
                session_id = f"wa_{normalized}"
                self._sessions[normalized] = {
                    "session_id": session_id,
                    "phone_raw": phone,
                    "created_at": datetime.now(),
                    "message_count": 0,
                }
                logger.info(f"[Sessions] Nueva sesión creada para {phone}: {session_id}")
            else:
                logger.debug(f"[Sessions] Sesión reutilizada para {phone}: {self._sessions[normalized]['session_id']}")

            self._sessions[normalized]["message_count"] += 1
            return self._sessions[normalized]["session_id"]

    def get_stats(self) -> dict:
        """Devuelve estadísticas de las sesiones activas (útil para /health)."""
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "sessions": [
                    {
                        "phone": v["phone_raw"],
                        "session_id": v["session_id"],
                        "messages": v["message_count"],
                        "created_at": v["created_at"].isoformat(),
                    }
                    for v in self._sessions.values()
                ],
            }

    def clear(self):
        """Limpia todas las sesiones (útil para tests)."""
        with self._lock:
            self._sessions.clear()


# Instancia global compartida entre el servidor y los workers
session_manager = WhatsAppSessionManager()
