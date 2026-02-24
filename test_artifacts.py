import asyncio
from agents.qwen_arquitecto.agent_core import LocalADKAgent

async def test_agent():
    print("Iniciando agente de prueba...")
    agent = LocalADKAgent()
    user_prompt = "Genera un script en Python muy básico para restar dos números. Usa [ARTEFACTO: python] y la herramienta asociada."
    response = await agent.run(user_input=user_prompt, session_id="test_artifact_session_02")
    print("--- RESPUESTA FINAL OBTENIDA POR EL SISTEMA ---")
    print(response)

if __name__ == "__main__":
    asyncio.run(test_agent())
