# Walkthrough: Integración WhatsApp ↔ Agente ADK/Qwen3

## ✅ Qué se ha implementado

Se ha creado el módulo `whatsapp_bridge/` en el branch `feature/whatsapp-bridge`, que actúa como puente entre WhatsApp y el agente local ADK/Qwen3.

**Archivos creados:**

| Archivo | Función |
|---|---|
| `whatsapp_bridge/config.py` | Carga credenciales Twilio y configuración del bridge desde `.env` |
| `whatsapp_bridge/twilio_client.py` | Wrapper async sobre el SDK oficial de Twilio |
| `whatsapp_bridge/session_manager.py` | Mapeo teléfono → sesión ADK (con historial persistente) |
| `whatsapp_bridge/server.py` | Servidor FastAPI receptor de webhooks Twilio |
| `whatsapp_bridge/run_bridge.py` | Punto de entrada con instrucciones de setup |
| `requirements.txt` | Dependencias del proyecto documentadas |

**Commit**: `feat: add WhatsApp bridge via Twilio Sandbox` en `feature/whatsapp-bridge`

---

## 🚀 Cómo ponerlo en marcha (setup completo)

### Paso 1 — Cuenta Twilio (5 min, gratis)
1. Ve a [twilio.com](https://twilio.com) y crea una cuenta gratuita
2. En la consola: **Messaging → Try it out → Send a WhatsApp message**
3. Verás el **QR del sandbox** → escanéalo con tu WhatsApp móvil
4. Copia tu **Account SID**, **Auth Token** y el número del sandbox

### Paso 2 — Configurar el `.env`
```bash
# Edita el .env en la raíz del proyecto:
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="tu_auth_token_aqui"
TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"  # número sandbox Twilio
```

### Paso 3 — Lanzar el bridge
```bash
# Terminal 1: activa el venv y lanza el bridge
cd "/Volumes/MisAppsV/Google _ADK"
source venv/bin/activate
python -m whatsapp_bridge.run_bridge
```

### Paso 4 — Exponer con ngrok  
```bash
# Terminal 2: crea el túnel HTTPS
brew install ngrok  # solo la primera vez
ngrok http 8001
# → Copia la URL: https://xxxx.ngrok-free.app
```

### Paso 5 — Conectar Twilio con el bridge
En **Twilio Console → Sandbox → "When a message comes in"**:
- Pega: `https://xxxx.ngrok-free.app/webhook`
- Método: `POST`
- Guarda

### Paso 6 — ¡Prueba!
Envía un mensaje de WhatsApp al número sandbox de Twilio → el agente Qwen3 responderá

---

## 🤖 Uso de Multi-Agentes (Novedad)

El bridge ahora permite hablar con diferentes agentes especializados sin cambiar de hilo. Usa estos comandos directamente en el chat de WhatsApp:

- `/agent coder`: Cambia al perfil de programador experto.
- `/agent researcher-bot`: Cambia al perfil con acceso a internet.
- `/agent quality-bot`: Cambia al perfil de QA y seguridad.
- `/agent arquitecto`: Vuelve al perfil general (por defecto).
- `/status`: Consulta qué agente te está respondiendo y tu ID de sesión.
- `/help`: Muestra la lista de comandos.

> 💡 **Persistencia:** El agente recordará qué perfil seleccionaste incluso si cierras la aplicación o reinicias el servidor.

---

## 🏗️ Arquitectura implementada

```
Tu teléfono (WhatsApp)
       ↓ mensaje
Servidores Twilio (API Meta oficial — SIN riesgo de ban)
       ↓ POST webhook HTTPS
ngrok (túnel local gratuito)
       ↓
FastAPI :8001  — whatsapp_bridge/server.py
       ↓ crea sesión por número de teléfono
LocalADKAgent (Qwen3 + Ollama) — historial persistente por usuario
       ↓ respuesta texto
FastAPI → Twilio API → Tu teléfono (WhatsApp)
```

---

## 🔍 Verificación realizada

- ✅ Sintaxis Python de los 6 módulos: sin errores
- ✅ SDK `twilio 9.10.2` instalado en el venv
- ✅ Commit creado: `[feature/whatsapp-bridge 70312769]`
- ✅ `main` branch intacto (el bridge está solo en `feature/whatsapp-bridge`)
