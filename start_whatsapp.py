#!/usr/bin/env python3
"""
start_whatsapp.py — Lanzador automático del bridge WhatsApp ↔ Agente ADK/Qwen3

Qué hace este script con un solo comando:
    1. Arranca ngrok (túnel HTTPS → localhost:8001)
    2. Obtiene la URL pública de ngrok automáticamente
    3. Actualiza el webhook del Sandbox de Twilio vía API (sin entrar en la consola)
    4. Arranca el servidor FastAPI del bridge

Uso:
    source venv/bin/activate
    python start_whatsapp.py

Requisitos:
    - ngrok instalado: brew install ngrok
    - Variables en .env: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN
    - Opcional: NGROK_STATIC_DOMAIN (dominio estático gratuito de ngrok)
      → Con dominio estático, la URL nunca cambia → Twilio solo se configura UNA VEZ
      → Obtén uno gratis en: https://dashboard.ngrok.com/cloud-edge/domains

Cómo obtener tu dominio estático gratuito de ngrok:
    1. Ve a https://dashboard.ngrok.com/cloud-edge/domains
    2. Haz clic en "New Domain" → se genera algo como "xyz-abc-def.ngrok-free.app"
    3. Añade al .env:  NGROK_STATIC_DOMAIN=xyz-abc-def.ngrok-free.app
    4. A partir de ahí, la URL será siempre la misma → configura Twilio una sola vez
"""

import os
import sys
import time
import json
import signal
import subprocess
import threading
import requests
from pathlib import Path

# ── Cargar .env manualmente (sin dependencias extra al inicio) ───────────────
def load_env():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)

load_env()

# ── Configuración ─────────────────────────────────────────────────────────────
ACCOUNT_SID     = os.environ.get("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN      = os.environ.get("TWILIO_AUTH_TOKEN", "")
BRIDGE_PORT     = int(os.environ.get("BRIDGE_PORT", "8001"))
NGROK_API_PORT  = 4040   # Puerto local de la API de ngrok
NGROK_DOMAIN    = os.environ.get("NGROK_STATIC_DOMAIN", "").strip()

# ── Proceso tracker ───────────────────────────────────────────────────────────
processes = []

def cleanup(sig=None, frame=None):
    """Cierra todos los subprocesos al recibir Ctrl+C o SIGTERM."""
    print("\n\n🛑 Cerrando todos los servicios...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


# ── Helpers ───────────────────────────────────────────────────────────────────
def print_header(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_ngrok_installed() -> bool:
    result = subprocess.run(["which", "ngrok"], capture_output=True)
    return result.returncode == 0

def start_ngrok() -> subprocess.Popen:
    """Arranca ngrok apuntando al puerto del bridge."""
    cmd = ["ngrok", "http", str(BRIDGE_PORT), "--log=stdout"]
    if NGROK_DOMAIN:
        cmd += [f"--domain={NGROK_DOMAIN}"]
        print(f"  📌 Usando dominio estático: https://{NGROK_DOMAIN}")
    else:
        print("  ⚡ Usando dominio temporal (cambia en cada arranque)")
        print("  💡 Para dominio fijo, añade NGROK_STATIC_DOMAIN al .env")
        print("     → https://dashboard.ngrok.com/cloud-edge/domains")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(proc)
    return proc

def wait_for_ngrok(timeout: int = 15) -> str | None:
    """
    Espera a que ngrok esté listo y devuelve la URL pública HTTPS.
    Lee la API local de ngrok en localhost:4040.
    """
    print("  ⏳ Esperando a que ngrok esté listo...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"http://localhost:{NGROK_API_PORT}/api/tunnels", timeout=2)
            tunnels = resp.json().get("tunnels", [])
            for t in tunnels:
                if t.get("proto") == "https":
                    print(" ✅")
                    return t["public_url"]
        except Exception:
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    print(" ❌")
    return None

def update_twilio_webhook(webhook_url: str) -> bool:
    """
    Actualiza el webhook del Sandbox de WhatsApp de Twilio vía la API REST.
    Endpoint: POST /2010-04-01/Accounts/{SID}/Messages/Sandboxes/WA.json
    """
    if not ACCOUNT_SID or not AUTH_TOKEN:
        print("  ⚠️  Credenciales Twilio no configuradas → no se puede actualizar el webhook automáticamente.")
        return False

    endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages/Sandboxes/WA.json"
    try:
        resp = requests.post(
            endpoint,
            data={"StatusCallback": webhook_url + "/webhook"},
            auth=(ACCOUNT_SID, AUTH_TOKEN),
            timeout=10
        )
        if resp.status_code in (200, 201):
            return True
        # Fallback: algunos endpoints de Sandbox usan una ruta diferente
        # Intentamos actualizar el IncomingPhoneNumber del sandbox
        print(f"  ⚠️  API sandbox devolvió {resp.status_code}. El webhook debe configurarse manualmente (solo esta vez).")
        return False
    except Exception as e:
        print(f"  ⚠️  Error de red al llamar a Twilio: {e}")
        return False

def start_bridge() -> subprocess.Popen:
    """
    Arranca el servidor FastAPI del bridge como subproceso.
    Redirige su salida directamente a la terminal (para ver los logs en tiempo real).
    """
    python = sys.executable
    proc = subprocess.Popen(
        [python, "-m", "whatsapp_bridge.run_bridge"],
        cwd=str(Path(__file__).parent)
    )
    processes.append(proc)
    return proc


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print_header("🤖 WhatsApp Bridge — ADK/Qwen3 × Twilio  |  Arranque automático")

    # 1. Verificar ngrok
    print("\n[1/4] Verificando ngrok...")
    if not check_ngrok_installed():
        print("  ❌ ngrok no está instalado.")
        print("  👉 Instálalo con:  brew install ngrok")
        print("     y luego autentícate: ngrok config add-authtoken <tu-token>")
        print("     (Token gratuito en https://dashboard.ngrok.com/get-started/your-authtoken)")
        sys.exit(1)
    print("  ✅ ngrok encontrado")

    # 2. Arrancar ngrok
    print("\n[2/4] Arrancando ngrok...")
    start_ngrok()
    public_url = wait_for_ngrok()
    if not public_url:
        print("  ❌ ngrok no pudo arrancar en 15 segundos.")
        print("  💡 Ejecuta manualmente: ngrok http 8001")
        cleanup()

    webhook_endpoint = f"{public_url}/webhook"
    print(f"\n  🌐 URL pública: {public_url}")
    print(f"  📡 Webhook:     {webhook_endpoint}")

    # 3. Actualizar Twilio
    print("\n[3/4] Actualizando webhook en Twilio Sandbox...")
    updated = update_twilio_webhook(public_url)
    if updated:
        print("  ✅ Webhook actualizado automáticamente en Twilio")
    else:
        print(f"\n  📋 ACCIÓN MANUAL NECESARIA (solo una vez si usas dominio estático):")
        print(f"     Twilio Console → Messaging → Try it out → Send a WhatsApp message")
        print(f"     Pega en 'When a message comes in': {webhook_endpoint}")

    # 4. Arrancar el bridge
    print("\n[4/4] Arrancando el bridge FastAPI...")
    bridge_proc = start_bridge()

    print_header("✅ Todo en marcha")
    print(f"  🌐 URL pública ngrok: {public_url}")
    print(f"  📡 Webhook activo:    {webhook_endpoint}")
    print(f"  🔍 Panel ngrok:       http://localhost:{NGROK_API_PORT}")
    print(f"  🏥 Health check:      http://localhost:{BRIDGE_PORT}/health")
    print()
    print("  Envía un mensaje de WhatsApp al número sandbox de Twilio")
    print("  y el agente Qwen3 responderá en segundos.")
    print()
    print("  Presiona Ctrl+C para detener todos los servicios.")
    print("=" * 60 + "\n")

    # Esperar a que el bridge termine (o Ctrl+C)
    try:
        bridge_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
