import os
from pathlib import Path
from typing import List, Optional
import shutil
import contextvars
from ddgs import DDGS
from pydantic import BaseModel, Field

current_session_var = contextvars.ContextVar('current_session_var', default="default_session")

from .config import settings

def _get_safe_path(file_path: str) -> Path:
    """Valida que el path esté dentro del workspace."""
    workspace = Path(settings.WORKSPACE_DIR).expanduser().resolve()
    target = (workspace / file_path).resolve()
    if not target.is_relative_to(workspace):
        raise PermissionError(f"Acceso denegado: {file_path} está fuera del sandbox.")
    return target

def list_files(directory: str = ".") -> str:
    """
    Lista los archivos y carpetas dentro del workspace del agente de forma superficial (no recursiva).
    NO USES ESTA HERRAMIENTA para leer o copiar proyectos enteros archivo por archivo.
    Argumento:
        directory: Carpeta a listar (relativa al workspace).
    """
    try:
        path = _get_safe_path(directory)
        if not path.exists():
            return f"Error: La carpeta {directory} no existe."
        
        items = os.listdir(path)
        if not items:
            return "La carpeta está vacía."
            
        # Límite de seguridad
        if len(items) > 50:
            return "\n".join(items[:50]) + f"\n... (y {len(items)-50} elementos más ocultos. No intentes leerlos todos a la vez)."
            
        return "\n".join(items)
    except Exception as e:
        return f"Error al listar archivos: {str(e)}"

def read_file(file_path: str) -> str:
    """
    Lee el contenido de un archivo de texto dentro del workspace.
    Argumento:
        file_path: Ruta del archivo (relativa al workspace).
    """
    try:
        path = _get_safe_path(file_path)
        if not path.is_file():
            return f"Error: {file_path} no es un archivo válido."
        
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error al leer archivo: {str(e)}"
def write_file(file_path: str, content: str) -> str:
    """
    Crea o sobreescribe un archivo con el contenido proporcionado.
    Argumentos:
        file_path: Ruta donde guardar el archivo (relativa al workspace).
        content: Contenido textual a escribir.
    """
    try:
        path = _get_safe_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Archivo '{file_path}' guardado correctamente en el workspace."
    except Exception as e:
        return f"Error al escribir archivo: {str(e)}"

def delete_file(file_path: str) -> str:
    """
    Elimina un archivo dentro del workspace.
    Argumento:
        file_path: Ruta del archivo (relativa al workspace).
    """
    try:
        path = _get_safe_path(file_path)
        if path.is_file():
            path.unlink()
            return f"Archivo '{file_path}' eliminado correctamente."
        elif path.is_dir():
            return f"Error: '{file_path}' es un directorio. Usa una herramienta específica para directorios si fuera necesario."
        else:
            return f"Error: El archivo '{file_path}' no existe."
    except Exception as e:
        return f"Error al eliminar archivo: {str(e)}"

def move_file(source_path: str, destination_path: str) -> str:
    """
    Mueve o renombra un archivo dentro del workspace. También sirve para mover archivos a subcarpetas.
    Argumentos:
        source_path: Ruta origen (relativa al workspace).
        destination_path: Ruta destino (relativa al workspace).
    """
    try:
        src = _get_safe_path(source_path)
        dst = _get_safe_path(destination_path)
        
        if not src.exists():
            return f"Error: El origen '{source_path}' no existe."
            
        # Crear carpetas de destino si no existen
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Usar shutil.move para soportar movimientos entre diferentes volúmenes
        shutil.move(str(src), str(dst))
        return f"Movido éxito: '{source_path}' -> '{destination_path}'."
    except Exception as e:
        return f"Error al mover archivo: {str(e)}"


from .memory_manager import memory_manager

def busqueda_web(query: str, max_results: int = 5) -> str:
    """
    Realiza una búsqueda web usando DuckDuckGo con persistencia en caché.
    Solo guarda en caché si hay resultados positivos para evitar bloqueos por fallos temporales.
    """
    try:
        query_norm = query.lower().strip()
        
        # 1. Recuperar de caché si existe (incluso si fue un fallo previo, para evitar bucles)
        cached = memory_manager.get_cached_search(query_norm)
        if cached:
            return f"[RESULTADO DE MEMORIA CACHÉ]\n{cached}"

        # 2. Búsqueda real
        import time
        time.sleep(1)
        
        print(f"!!! [DEBUG] Herramienta busqueda_web ejecutándose para la query: '{query}' !!!")
        with DDGS() as ddgs:
            # Buscamos con un lenguaje y región más genéricos/amplios
            results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                summary = f"No se han encontrado resultados web para '{query}'. Por favor, intenta con términos más simples o verifica la conexión."
                memory_manager.save_search(query_norm, summary)
                return summary
            
            output = ["Estos son resúmenes cortos de los resultados de búsqueda. Si necesitas más contexto para responder de forma precisa, DEBES usar la herramienta leer_pagina_web con el 'Enlace' que parezca más relevante.\n"]
            for r in results:
                body = r.get('body', 'Sin resumen')
                if len(body) > 300:
                    body = body[:300] + "..."
                output.append(f"Título: {r.get('title', 'Sin título')}\nResumen: {body}\nEnlace: {r.get('href', '')}")
            
            summary = "\n---\n".join(output)
            
            # 3. Guardar en caché siempre
            memory_manager.save_search(query_norm, summary)
            
            return summary
    except Exception as e:
        return f"Error en búsqueda web: {str(e)}. Intenta de nuevo en unos segundos."

import requests
from bs4 import BeautifulSoup

def leer_pagina_web(url: str) -> str:
    """
    Lee y extrae el contenido de texto principal de una página web.
    Útil cuando los resúmenes de resultados de búsqueda web son demasiado cortos.
    Argumento:
        url: La dirección URL de la página a leer (obtenida de la búsqueda web).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar scripts, estilos, navegaciones y otros elementos de UI
        for element in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
            element.extract()
            
        # Extraer texto limpio
        text = soup.get_text(separator='\n')
        
        # Limpiar líneas en blanco excesivas para ser eficientes con tokens
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limitar longitud a ~5000 caracteres para no saturar el contexto
        max_chars = 5000 
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n...[Contenido truncado por longitud excesiva]"
            
        return f"[CONTENIDO LEÍDO DE {url}]\n\n{text}"
    except Exception as e:
        return f"Error al intentar leer la página web {url}: {str(e)}"

def consultar_historial(termino_busqueda: str) -> str:
    """
    Consulta los 'recuerdos' del agente (historial previo, resúmenes y búsquedas pasadas).
    Argumento:
        termino_busqueda: El concepto o información que se desea recordar.
    """
    try:
        return memory_manager.search_past_memories(termino_busqueda)
    except Exception as e:
        return f"Error al consultar historial: {str(e)}"

def exportar_artefacto(titulo: str, tecnologia: str, version: str, ruta_guardado: str, contenido: str, nombre_proyecto: str = "Proyecto_General") -> str:
    """
    Exporta un artefacto generado por el agente al disco duro.
    TODOS los argumentos deben ser strings simples (texto). No uses JSON ni estructuras anidadas aquí.
    IMPORTANTE: Una vez utilices esta herramienta con éxito, DEBES FINALIZAR TU TAREA Y RESPONDER AL USUARIO informando que se ha guardado. NO VUELVAS A LLAMAR A ESTA HERRAMIENTA REPETIDAMENTE para el mismo contenido.
    Argumentos:
        titulo: Título descriptivo del artefacto.
        tecnologia: Tecnología principal utilizada (ej. 'Python', 'Markdown').
        version: Versión del artefacto, e.g., '1.0'.
        ruta_guardado: Nombre de archivo sugerido con extensión correcta, ej: 'script.py'.
        contenido: El código o texto completo del artefacto.
        nombre_proyecto: Nombre corto representativo del proyecto global (ej. 'Capsula_Seguridad'). Solo se usará para nombrar la carpeta inteligente de la sesión.
    """
    try:
        session_id = current_session_var.get()
        workspace = Path(settings.WORKSPACE_DIR).expanduser().resolve()
        base_dir = workspace / "Proyectos_Agente"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de enlace para unificar todos los artefactos de la sesión en la misma subcarpeta
        link_file = base_dir / f".session_{session_id}.txt"
        
        if link_file.exists():
            folder_name = link_file.read_text(encoding="utf-8").strip()
        else:
            from datetime import datetime
            import re
            fecha_str = datetime.now().strftime("%Y-%m-%d")
            clean_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', nombre_proyecto)
            folder_name = f"{fecha_str}_{clean_name}"
            link_file.write_text(folder_name, encoding="utf-8")
            
        project_dir = base_dir / folder_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo
        file_path = project_dir / ruta_guardado
        file_path.write_text(contenido, encoding="utf-8")
        
        # Actualizar índice README.md
        readme_path = project_dir / "README.md"
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not readme_path.exists():
            readme_path.write_text(f"# Índice de Artefactos\n\nSesión: `{session_id}`\n\n| Título | Tecnología | Versión | Archivo | Fecha |\n|---|---|---|---|---|\n", encoding="utf-8")
        
        with open(readme_path, "a", encoding="utf-8") as f:
            f.write(f"| {titulo} | {tecnologia} | {version} | [{ruta_guardado}](./{ruta_guardado}) | {fecha} |\n")
            
        internal_stop = "\n\n[INSTRUCCIÓN INTERNA DEL SISTEMA: EL ARTEFACTO SE HA GUARDADO CON ÉXITO. TIENES ESTRICTAMENTE PROHIBIDO VOLVER A LLAMAR A ESTA HERRAMIENTA PARA EL MISMO ARCHIVO. FINALIZA TU TURNO AHORA Y RESPONDE AL USUARIO EN EL CHAT.]"
        return f"Artefacto guardado exitosamente en {file_path}. Índice README actualizado.{internal_stop}"
    except Exception as e:
        return f"Error al exportar artefacto: {str(e)}"

def extraer_resumen_web(url: str) -> str:
    """
    Descarga una página web, limpia el código basura (scripts/estilos) y devuelve una
    instrucción interna obligando al agente a producir un resumen técnico profundo.
    Argumento:
        url: URL de la página web a resumir.
    """
    try:
        print(f"!!! [DEBUG] Herramienta extraer_resumen_web ejecutándose para la URL: '{url}' !!!")
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar scripts, estilos, navegaciones triviales
        for element in soup(["script", "style", "header", "footer", "nav", "aside", "form", "svg", "button"]):
            element.extract()
            
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        text = '\n'.join(chunk for line in lines for chunk in line.split("  ") if chunk)
        
        if len(text) > 8000:
            text = text[:8000] + "\n\n...[Contenido truncado]"

        instruccion_interna = (
            f"\n\n[INSTRUCCIÓN DEL SISTEMA DE OBLIGATORIO CUMPLIMIENTO]: "
            f"Lee detenidamente la información anterior extraída de la URL {url}. "
            f"Debes generar INMEDIATAMENTE un Resumen Técnico estructurado y EXTREMADAMENTE CONCISO (ve directo al grano, usando viñetas o bullet points) en tu respuesta. "
            f"NOTA CRÍTICA: Si eres un agente secundario o delegado, FINALIZA TU TAREA entregando este resumen puro, SIN PREGUNTAR AL USUARIO ni intentar usar herramientas de guardado."
        )
        return f"[CONTENIDO LIMPIO EXTRAÍDO]\n\n{text}{instruccion_interna}"
        
    except Exception as e:
        return f"Error al intentar extraer el resumen de la web {url}: {str(e)}"

async def delegar_tarea(tarea: str, contexto: str, perfil: str = "coder") -> str:
    """
    Delega una subtarea a un Agente Secundario especializado y devuelve su respuesta FINAL INMEDIATAMENTE.
    IMPORTANTE: La llamada bloqueará tu ejecución hasta que el agente termine. Una vez recibas el resultado de esta herramienta, DEBES considerarlo como el resultado FINAL y COMPLETO de la tarea.
    NO EXISTE NINGUNA HERRAMIENTA PARA "CONSULTAR EL ESTADO" DE LAS TAREAS. PROHIBIDO intentar usar herramientas como 'consultar_resultados_tareas'.
    Argumentos:
        tarea: Descripción clara de lo que el agente secundario debe hacer.
        contexto: Información relevante, código o texto necesario para realizar la tarea.
        perfil: El rol del agente secundario ('coder', 'quality-bot', 'researcher-bot'). Por defecto 'coder'.
    """
    try:
        from .agent_core import LocalADKAgent
        import uuid
        
        caller_session = current_session_var.get()
        print(f"!!! [DEBUG] La sesión {caller_session} está llamando a delegar_tarea({perfil}) !!!")
        
        if perfil not in ["coder", "quality-bot", "researcher-bot"]:
            perfil = "coder"
            
        print(f"[*] Delegando tarea al perfil: {perfil}...")
        
        sub_agent = LocalADKAgent(profile=perfil)
        prompt = f"TAREA:\n{tarea}\n\nCONTEXTO:\n{contexto}"
        sub_session_id = f"delegated_{perfil}_{uuid.uuid4().hex[:8]}"
        
        resultado = await sub_agent.run(prompt, session_id=sub_session_id)
        
        print(f"!!! [DEBUG] Resultado del sub-agente:\n{resultado}\n!!!")
        
        internal_stop = "\n\n[INSTRUCCIÓN INTERNA DEL SISTEMA: LA TAREA HA SIDO DELEGADA Y ESTE ES EL RESULTADO FINAL COMPLETO. NO EXISTEN HERRAMIENTAS PARA CONSULTAR EL ESTADO (NO INTENTES INVENTARLAS). CONTINÚA DIRECTAMENTE CON EL SIGUIENTE PASO DE TU PLAN BASÁNDOTE EN ESTA RESPUESTA O HABLA CON EL USUARIO.]"
        return f"[RESULTADO DEL AGENTE SECUNDARIO - Perfil: {perfil}]\n\n{resultado}{internal_stop}"
        
    except Exception as e:
        return f"Error al delegar tarea: {str(e)}"

# Herramientas estables para Qwen Architect
from .gcal_tools import consultar_agenda, agendar_revision
from .notion_tools import publicar_proyecto_notion, publicar_en_notion

TOOLS = [list_files, read_file, write_file, delete_file, move_file, busqueda_web, leer_pagina_web, extraer_resumen_web, consultar_historial, exportar_artefacto, consultar_agenda, agendar_revision, publicar_proyecto_notion, publicar_en_notion, delegar_tarea]

