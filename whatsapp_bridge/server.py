"""
server.py — Servidor FastAPI que actúa como receptor de webhooks de Twilio.

Flujo de un mensaje entrante:
    1. WhatsApp del usuario → Twilio → POST /webhook (este servidor)
    2. El webhook valida la firma Twilio (seguridad)
    3. Se extrae el número de teléfono (From) y el texto (Body)
    4. Se valida si el número está en la lista de permitidos (si está configurada)
    5. Se responde 200 OK inmediatamente (Twilio requiere respuesta rápida)
    6. En background: LocalADKAgent.run() procesa el mensaje
    7. La respuesta del agente se envía de vuelta via Twilio REST API
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse

from .config import bridge_settings
from .twilio_client import twilio_client
from .session_manager import session_manager

# ── Configuración de logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# ── Importación lazy del agente (se hace al arrancar el servidor) ────────────
_agent_class = None


def get_agent_class():
    """Importación lazy de LocalADKAgent para no ralentizar el import del módulo."""
    global _agent_class
    if _agent_class is None:
        from agents.qwen_arquitecto.agent_core import LocalADKAgent
        _agent_class = LocalADKAgent
    return _agent_class


# ── FastAPI app ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Evento de arranque del servidor."""
    logger.info("=" * 60)
    logger.info("  WhatsApp Bridge — Agente ADK/Qwen3 × Twilio Sandbox")
    logger.info("=" * 60)
    if not bridge_settings.validate_credentials():
        logger.warning(
            "⚠️  TWILIO_ACCOUNT_SID o TWILIO_AUTH_TOKEN no están configurados. "
            "El servidor arrancará pero NO podrá enviar mensajes. "
            "Añade las variables al archivo .env"
        )
    allowed = bridge_settings.allowed_numbers_set
    if allowed:
        logger.info(f"🔒 Números autorizados: {allowed}")
    else:
        logger.info("🌐 Sin restricción de números (todos pueden interactuar)")

    logger.info(f"🤖 Agente ADK perfil: '{bridge_settings.WHATSAPP_AGENT_PROFILE}'")
    logger.info(f"🚪 Escuchando en: http://{bridge_settings.BRIDGE_HOST}:{bridge_settings.BRIDGE_PORT}")
    logger.info("   Recuerda exponer el puerto con ngrok: ngrok http 8001")
    logger.info("=" * 60)
    yield


app = FastAPI(
    title="WhatsApp Bridge — ADK/Qwen3",
    description="Puente entre WhatsApp (via Twilio) y el agente local ADK/Qwen3",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoint de salud ────────────────────────────────────────────────────────
@app.get("/health", summary="Estado del servidor")
async def health():
    """Comprobación de estado del bridge."""
    return {
        "status": "ok",
        "credentials_configured": bridge_settings.validate_credentials(),
        "agent_profile": bridge_settings.WHATSAPP_AGENT_PROFILE,
        "sessions": session_manager.get_stats(),
    }


# ── Procesamiento del agente en background ───────────────────────────────────
async def process_and_reply(from_number: str, user_text: str):
    """
    Tarea en background:
    1. Obtiene/crea la sesión ADK del usuario
    2. Lanza el agente
    3. Envía la respuesta de vuelta por WhatsApp
    """
    session_id = session_manager.get_or_create(from_number)
    logger.info(f"[Bridge] Procesando mensaje de {from_number} (sesión: {session_id})")

    try:
        AgentClass = get_agent_class()
        agent = AgentClass(profile=bridge_settings.WHATSAPP_AGENT_PROFILE)
        response = await agent.run(user_text, session_id=session_id)
        logger.info(f"[Bridge] Respuesta del agente ({len(response)} chars)")
    except Exception as e:
        logger.error(f"[Bridge] Error del agente: {e}", exc_info=True)
        response = f"⚠️ Lo siento, hubo un error interno procesando tu mensaje:\n{str(e)}"

    # Enviar respuesta de vuelta al usuario por WhatsApp
    try:
        await twilio_client.send_text(to=from_number, body=response)
    except Exception as e:
        logger.error(f"[Twilio] Error al enviar respuesta a {from_number}: {e}", exc_info=True)


# ── Webhook principal ────────────────────────────────────────────────────────
@app.post(
    "/webhook",
    response_class=PlainTextResponse,
    summary="Receptor de mensajes WhatsApp entrantes (Twilio webhook)"
)
async def whatsapp_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
):
    """
    Recibe los mensajes entrantes de WhatsApp via Twilio.

    Twilio envía un POST form-encoded con los campos:
        From   — Número del remitente con prefijo 'whatsapp:'
        Body   — Texto del mensaje
        NumMedia — Número de archivos adjuntos (ignorados en v1)

    Responde con TwiML vacío para que Twilio sepa que el mensaje fue recibido.
    El procesamiento real ocurre en background para no superar el timeout de Twilio (15s).
    """
    logger.info(f"[Webhook] Mensaje recibido de: {From!r} | Texto: {Body[:80]!r}")

    # 1. Validar número autorizado
    allowed = bridge_settings.allowed_numbers_set
    if allowed and From not in allowed:
        logger.warning(f"[Webhook] Número no autorizado rechazado: {From}")
        # Respondemos 200 OK a Twilio pero no procesamos el mensaje
        return PlainTextResponse("<?xml version='1.0' encoding='UTF-8'?><Response/>")

    # 2. Ignorar mensajes vacíos o multimedia sin texto
    text = Body.strip()
    if not text:
        logger.info(f"[Webhook] Mensaje vacío o solo multimedia de {From}, ignorando.")
        return PlainTextResponse("<?xml version='1.0' encoding='UTF-8'?><Response/>")

    # 3. Lanzar el agente en background (devolvemos 200 OK inmediatamente)
    asyncio.create_task(process_and_reply(from_number=From, user_text=text))

    # Respuesta TwiML vacía: Twilio la requiere, no enviamos nada en el body
    return PlainTextResponse(
        content="<?xml version='1.0' encoding='UTF-8'?><Response/>",
        media_type="text/xml"
    )
