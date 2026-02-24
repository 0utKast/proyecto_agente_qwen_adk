import asyncio
from agents.qwen_arquitecto.agent_core import LocalADKAgent

async def test():
    print("Inicializando agente...")
    try:
        agent = LocalADKAgent()
        print("Agente cargado. Enviando mensaje...")
        
        async for chunk in agent.run("Revisa mi agenda para el lunes 23 de febrero de 2026 y proponme un hueco libre de 30 minutos."):
            t = chunk.get("type")
            if t == "text":
                print(chunk.get("content", ""), end="", flush=True)
            elif t == "tool_call":
                print(f"\\n[Herramienta Invocada: {chunk.get('name')}]\\n")
            elif t == "thought":
                print(f"\\n[Trace]: {chunk.get('content')}\\n")
    except Exception as e:
        print(f"\\nERROR EN TEST: {e}")

if __name__ == "__main__":
    asyncio.run(test())
