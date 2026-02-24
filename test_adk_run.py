import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from agents.qwen_arquitecto.agent import root_agent

async def main():
    print("Iniciando prueba de agente completo...")
    
    # We yield from the agent to see exactly what chunks it produces
    try:
        async for chunk in root_agent.run("Busca en la web la librería python más rápida para monitorizar sistema de archivos"):
            print(f"CHUNK TYPE: {type(chunk)}")
            if hasattr(chunk, 'text'):
                print(f"TEXT: {chunk.text!r}")
            elif hasattr(chunk, 'name'):
                print(f"TOOL CALL: {chunk.name} args: {getattr(chunk, 'args', '')}")
            else:
                print(f"CHUNK: {chunk}")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
