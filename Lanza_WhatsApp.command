#!/bin/bash
# Lanza_WhatsApp.command — Acceso directo para arrancar el Agente WhatsApp
# Autor: Antigravity

# 1. Ir a la carpeta del proyecto
cd "/Volumes/MisAppsV/Google _ADK"

# 2. Activar el entorno virtual
source venv/bin/activate

# 3. Lanzar el bridge automatizado
python3 start_whatsapp.py

# Si el proceso termina, mantener la ventana abierta para ver posibles errores
echo ""
echo "----------------------------------------------------"
echo "El proceso ha terminado. Presiona cualquier tecla para cerrar."
read -n 1
