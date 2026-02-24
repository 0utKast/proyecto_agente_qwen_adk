import asyncio
import os
import sys
import logging

sys.path.insert(0, os.path.abspath('.'))
from agents.qwen_arquitecto.agent_core import LocalADKAgent
from litellm import set_verbose

set_verbose=True
os.environ["LITELLM_LOG"] = "DEBUG"
logging.basicConfig(level=logging.DEBUG)

async def main():
    agent = LocalADKAgent()
    print("Iniciando agente de prueba con DEBUG...")
    
    prompt = "Busca en la web la librería de Python más eficiente actualmente para observar cambios en el sistema de archivos de forma asíncrona."
    
    response = await agent.run(prompt, "test_session_toolcall")
    print("\n--- RESPUESTA FINAL ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
