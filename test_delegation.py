import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from agents.qwen_arquitecto.agent_core import LocalADKAgent

async def main():
    print("Iniciando prueba de orquestación multi-agente...")
    
    # Instanciamos al agente principal (arquitecto)
    arquitecto = LocalADKAgent(profile="arquitecto")
    
    prompt = "Por favor, invoca la herramienta delegar_tarea para pedirle al perfil 'coder' que escriba una función en Python para calcular el factorial de un número. UNA VEZ que la herramienta te devuelva el resultado, despídete y FINALIZA tu respuesta. ¡ES MUY IMPORTANTE QUE NO VUELVAS A LLAMAR A LA HERRAMIENTA!"
    
    print(f"\n[PROMPT PARA EL ARQUITECTO]:\n{prompt}\n")
    print("-" * 50)
    
    try:
        resultado = await arquitecto.run(prompt, session_id="test_orchestration_01")
        print("\n[RESPUESTA FINAL DEL ARQUITECTO]:")
        print(resultado)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
