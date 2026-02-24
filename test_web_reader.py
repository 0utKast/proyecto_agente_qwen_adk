import sys
import os

sys.path.insert(0, os.path.abspath('.'))
from agents.qwen_arquitecto.tools import busqueda_web_ddg, leer_pagina_web

def test_search():
    print("Probando busqueda_web_ddg con una consulta que requiere contexto...")
    resultado_busqueda = busqueda_web_ddg("python list comprehension", max_results=3)
    print("\n--- RESULTADOS BÚSQUEDA ---")
    print(resultado_busqueda)
    
    # Probar leer una web directamente
    print("\nProbando leer_pagina_web con url especifica...")
    url = "https://es.wikipedia.org/wiki/Python"
    resultado_lectura = leer_pagina_web(url)
    print("\n--- RESULTADO LECTURA (primeros 500 caracteres) ---")
    print(resultado_lectura[:500])

if __name__ == "__main__":
    test_search()
