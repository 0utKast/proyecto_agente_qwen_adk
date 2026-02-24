import asyncio
import sys
import os

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

from agents.qwen_arquitecto.agent_core import LocalADKAgent
from agents.qwen_arquitecto.config import settings

async def test_persistence():
    agent = LocalADKAgent()
    session_id = "test_session_123"
    
    print("\n--- PASO 1: Guardando información específica ---")
    user_input1 = "Hola, mi lenguaje de programación favorito es Rust y estoy trabajando en un proyecto de Google ADK."
    response1 = await agent.run(user_input1, session_id=session_id)
    print(f"Agente: {response1}")
    
    print("\n--- PASO 2: Recuperando información en nueva sesión ---")
    # Simulamos el cierre y apertura creando una nueva instancia o simplemente usando el mismo ID
    user_input2 = "¿Cuál es mi lenguaje de programación favorito y en qué tipo de proyecto trabajo según lo que te dije antes?"
    response2 = await agent.run(user_input2, session_id=session_id)
    print(f"Agente (Recuerdo): {response2}")

if __name__ == "__main__":
    asyncio.run(test_persistence())
