#!/bin/bash

# Exit on error
set -e

echo "🚀 Iniciando configuración de Agente Local ADK..."

# 1. Verificar Ollama
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama no está instalado. Por favor, instálalo desde https://ollama.com/"
    exit 1
fi

echo "✅ Ollama detectado."

# 2. Configurar hardware (M4 Pro optimization)
export OLLAMA_NUM_GPU=1
echo "⚙️ Configuración de GPU para M4 Pro activa (OLLAMA_NUM_GPU=1)."

# 3. Descargar modelos necesarios
echo "📥 Descargando modelos de Ollama..."
ollama pull qwen2.5-coder
ollama pull llama3.1
echo "✅ Modelos listos."

# 4. Crear entorno virtual de Python
echo "🐍 Configurando entorno virtual con Python 3.11..."
# Si existe venv con Python anterior, lo borramos para asegurar limpieza
if [ -d "venv" ]; then
    rm -rf venv
fi
/opt/homebrew/bin/python3.11 -m venv venv

source venv/bin/activate

# 5. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install google-adk litellm ollama fastapi uvicorn python-multipart pydantic-settings ddgs

echo "✅ Instalación completada con éxito."
echo "💡 Para activar el entorno manualmente: source venv/bin/activate"
