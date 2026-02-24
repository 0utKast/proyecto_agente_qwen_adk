import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
from agents.qwen_arquitecto.agent_core import LocalADKAgent
from agents.qwen_arquitecto.config import settings

async def main():
    agent = LocalADKAgent()
    print("Iniciando agente de prueba...")
    
    prompt = """
    Voy a crear un artefacto con un ejemplo simple de cómo usar la librería watchdog para monitorear cambios en el
    sistema de archivos.

    Basándote en esa librería, genera un script de Python llamado sincronizador_local.py. El script debe copiar
    archivos de una carpeta 'Origen' a una 'Destino' cuando detecte cambios. Crea también un documento técnico
    en Markdown explicando cómo configurarlo. Recuerda usar el formato de artefactos y generar los metadatos
    JSON correspondientes.
    """
    
    response = await agent.run(prompt, "test_session_watchdog")
    print("\n--- RESPUESTA FINAL ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
