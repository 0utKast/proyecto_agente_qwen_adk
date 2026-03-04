# Integración WhatsApp ↔ Agente ADK/Qwen3

## Análisis de Viabilidad

La integración es **totalmente viable**. El agente ya tiene una arquitectura modular que facilita añadir canales de entrada/salida: basta con crear una capa de "puente" entre WhatsApp y el `LocalADKAgent`.

---

## Aclaración: OpenClaw y otras APIs no oficiales

> [!CAUTION]
> **OpenClaw, WAHA, `whatsapp-web.js` y Baileys utilizan exactamente el mismo mecanismo técnico**: simulan una sesión de WhatsApp Web escaneando un QR. Desde el punto de vista de Meta, esto es indistinguible de un bot no autorizado y **viola los Términos de Servicio de WhatsApp**, con riesgo de ban permanente del número. No hay ninguna de estas herramientas que sea "segura" en este sentido. El hecho de que no lo anuncien no significa que no haya riesgo.

Para un tutorial público en el que los seguidores van a usar su número personal, la única opción éticamente responsable es un método **oficialmente sancionado por Meta**.

---

## Opciones Seguras (Riesgo Ban = 0)

| Opción | Coste desarrollo | Complejidad | QR para unirse | Ideal para tutorial |
|--------|-----------------|-------------|---------------|---------------------|
| **Meta Cloud API + sandbox de desarrollo** | Gratis (sandbox ilimitado) | Media | ❌ (token API) | ✅ Sí |
| **Twilio WhatsApp Sandbox** | Gratis (testing) | Baja | ✅ | ✅✅ Muy fácil |
| **Twilio WhatsApp (producción)** | Desde ~$0.005/msg | Baja | ❌ | ✅ Sí |

### ✅ Recomendación principal: **Twilio WhatsApp Sandbox**

**¿Por qué Twilio Sandbox para el tutorial?**
- Tiene un **QR real para escanear** que une tu número al sandbox en segundos.
- Cuenta de Twilio gratuita, sin tarjeta de crédito para el sandbox.
- SDK Python oficial (`twilio`), con documentación excelente.
- **Cero riesgo de ban**: usa la Meta Cloud API oficial por debajo.
- Setup completo en ~10 minutos, perfecto para un vídeo.
- Para pasar a producción después, solo se cambia el número Twilio por uno dedicado aprobado.

### 🥈 Alternativa: **Meta Cloud API directa**

- Sin intermediarios, pero requiere cuenta de Meta for Developers + `ngrok` para webhooks locales.
- El sandbox de desarrollo de Meta incluye un **número de test gratuito** que no necesita aprobación.
- Ligeramente más complejo de configurar que Twilio, pero 100% gratuito y oficial.

---

## Arquitectura Propuesta (con Twilio Sandbox)

```
Tu teléfono (WhatsApp)
        ↓ mensaje
  Servidores Twilio (API oficial Meta)
        ↓ POST webhook HTTPS
   ngrok (túnel HTTPS local, solo desarrollo)
        ↓
   FastAPI Bridge (:8001)  ←—  whatsapp_bridge/server.py
        ↓ crea/reutiliza sesión
   LocalADKAgent (Qwen3 + Ollama)
        ↓ respuesta texto
   FastAPI Bridge
        ↓ POST twilio REST API
  Servidores Twilio
        ↓ entrega mensaje
Tu teléfono (WhatsApp)
```

> [!NOTE]
> `ngrok` se usa **solo en desarrollo local** para exponer el bridge al webhook de Twilio. En producción, el servidor estaría en una IP pública (o un VPS simple). Para el tutorial, ngrok es gratuito y tiene una UI Web que muestra cada request en tiempo real, lo que es visualmente útil.

---

## Proposed Changes

### Branch de trabajo

#### [NEW] Crear branch `feature/whatsapp-bridge`
```bash
git checkout -b feature/whatsapp-bridge
```

---

### Módulo `whatsapp_bridge/` (nuevo)

#### [NEW] `whatsapp_bridge/__init__.py`
Vacío.

#### [NEW] `whatsapp_bridge/config.py`
Variables de configuración cargadas de `.env`:
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER` (el número sandbox de Twilio, ej: `whatsapp:+14155238886`)
- `BRIDGE_PORT` (default: `8001`)
- `ALLOWED_PHONE_NUMBERS` (lista de números autorizados, vacío = todos)

#### [NEW] `whatsapp_bridge/twilio_client.py`
Wrapper sobre el SDK oficial de Twilio:
- `send_text(to_number, text)` → llama a `client.messages.create(...)`

#### [NEW] `whatsapp_bridge/session_manager.py`
Mapeo de número de teléfono a sesión del agente ADK:
- `get_or_create_session(phone)` → devuelve `session_id` (crea si no existe)
- Dict en memoria + opcionalmente persistido en SQLite

#### [NEW] `whatsapp_bridge/server.py`
Servidor **FastAPI** que recibe los webhooks de Twilio:
- `POST /webhook` → valida la firma Twilio, extrae `From` y `Body`, lanza `LocalADKAgent.run()` en background, responde `200 OK` con `<Response/>` (TwiML vacío).
- `GET /health` → comprobación de estado.
- El agente responde asíncronamente y llama a `twilio_client.send_text()` con el resultado.

#### [NEW] `whatsapp_bridge/run_bridge.py`
Script de entrada del servidor FastAPI.

#### [NEW] `start_whatsapp.py` (Script de automatización)
Lanzador único que:
1. Arranca ngrok.
2. Obtiene la URL pública automáticamente.
3. Actualiza el webhook de Twilio vía API.
4. Lanza el bridge.
Soporta `NGROK_STATIC_DOMAIN` para URLs permanentes.

---

### Herramienta de túnel HTTPS (solo desarrollo)

`ngrok` se instala una única vez (`brew install ngrok`) y se usa para exponer el bridge:
```bash
ngrok http 8001
# → obtienes una URL tipo https://abc123.ngrok-free.app
# Esa URL se pega en el Twilio Sandbox como webhook
```

---

### Actualizaciones al proyecto existente

#### [MODIFY] `.env` / `.env.example`
Añadir las nuevas variables:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
BRIDGE_PORT=8001
ALLOWED_PHONE_NUMBERS=
```

#### [MODIFY] `README.md`
Añadir sección "Integración WhatsApp" con instrucciones de configuración y escaneo de QR.

#### [NEW] Soporte Multi-Agente
Comandos implementados en el chat de WhatsApp:
- `/agent <arquitecto|coder|researcher-bot|quality-bot>`: Cambia de agente.
- `/status`: Consulta el perfil activo.
- `/help`: Muestra los comandos.
Persistencia de perfil por número de teléfono en `session_manager.py`.

---

## Dependencias nuevas a instalar

```
fastapi
uvicorn[standard]
twilio
```

Añadir a `requirements.txt` (sólo en el branch).

---

## Verification Plan

### Setup previo (una sola vez, ~10 minutos)
1. Crear cuenta gratuita en [twilio.com](https://twilio.com).
2. Ir a **Messaging > Try it out > Send a WhatsApp message** → aparece el QR.
3. Escanear el QR con WhatsApp móvil para unirse al sandbox.
4. Instalar y lanzar ngrok: `ngrok http 8001`.
5. Pegar la URL de ngrok en el campo **"When a message comes in"** del Sandbox de Twilio.
6. Lanzar el bridge: `python -m whatsapp_bridge.run_bridge`.

### Pruebas automatizadas
- **Test unitario** `whatsapp_bridge/test_twilio_client.py`: mockealar el SDK de Twilio con `unittest.mock` y verificar que `send_text()` llama a `messages.create()` con los parámetros correctos.
- **Test de integración** (`test_bridge_webhook.py`): usar `fastapi.testclient.TestClient` para enviar un payload simulado de Twilio y verificar respuesta `200` y que el mock del agente es invocado.

### Verificación manual
1. Enviar un mensaje de WhatsApp al número sandbox de Twilio desde tu teléfono.
2. En los logs del bridge, debe aparecer el mensaje recibido.
3. El agente Qwen procesa y responde; el mensaje llega de vuelta a tu WhatsApp.
4. En el panel de Twilio, los logs muestran el mensaje enviado correctamente con estado `delivered`.
