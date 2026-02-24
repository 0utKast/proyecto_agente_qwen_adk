import asyncio
from agents.qwen_arquitecto.agent_core import LocalADKAgent

async def main():
    print("Iniciando prueba aislada de Researcher-Bot...")
    
    # Instanciamos al agente secundario directamente
    researcher = LocalADKAgent(profile="researcher-bot")
    
    prompt = "Busca las mejores prácticas para prevenir ataques de Inyección SQL en Python 2026. Usa busqueda_web y extraer_resumen_web. Una vez que tengas un informe, finaliza y devuélvelo."
    
    print(f"\n[PROMPT PARA EL RESEARCHER]:\n{prompt}\n")
    print("-" * 50)
    
    resultado = await researcher.run(prompt, session_id="test_researcher_loop_01")
    
    print("\n" + "=" * 50)
    print("[RESPUESTA FINAL DEL RESEARCHER]:")
    print(resultado)

if __name__ == "__main__":
    asyncio.run(main())
