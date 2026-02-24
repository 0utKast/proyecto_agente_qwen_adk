import os
import glob
from pathlib import Path
import requests

from .config import settings
def publicar_proyecto_notion(titulo_pagina: str) -> str:
    """
    Sincroniza los artefactos locales de la sesión actual hacia Notion,
    creando una nueva página estructurada con los bloques de código y Tabla de Contenidos.
    Argumento:
        titulo_pagina: El título que tendrá la nueva página en Notion.
    """
    notion_api_key = os.getenv('NOTION_API_KEY')
    parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')
    
    # Deferred import to prevent circular dependency
    from .tools import current_session_var

    if not notion_api_key or not parent_page_id:
        return ("⚠️ Error de Configuración de Notion: Faltan las variables de entorno "
                "'NOTION_API_KEY' o 'NOTION_PARENT_PAGE_ID'. Por favor, añádelas a tu archivo .env.")

    # Sanitizar Page ID (por si el usuario pegó la URL completa o el título-id)
    if "notion.so" in parent_page_id or "notion.site" in parent_page_id:
        parent_page_id = parent_page_id.split("/")[-1].split("?")[0].split("-")[-1]
    elif "-" in parent_page_id:
        parent_page_id = parent_page_id.split("-")[-1]

    # Convertir a formato UUID (8-4-4-4-12) si es una cadena de 32 caracteres
    if len(parent_page_id) == 32:
        parent_page_id = f"{parent_page_id[:8]}-{parent_page_id[8:12]}-{parent_page_id[12:16]}-{parent_page_id[16:20]}-{parent_page_id[20:]}"

    session_id = current_session_var.get()
    workspace = Path(settings.WORKSPACE_DIR).expanduser().resolve()
    project_dir = workspace / "Proyectos_Agente" / session_id

    if not project_dir.exists():
        return f"No se encontró el directorio de proyectos para la sesión actual: {project_dir}"

    # Recopilar todos los archivos en la carpeta del proyecto
    # Excluyendo carpetas ocultas o __pycache__ si las hubiera (generalmente no en artefactos)
    archivos = []
    for filepath in project_dir.rglob('*'):
        if filepath.is_file() and not filepath.name.startswith('.'):
            archivos.append(filepath)

    if not archivos:
        return "No hay artefactos exportados en esta sesión para publicar en Notion."

    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Bloques iniciales: Tabla de Contenidos
    children_blocks = [
        {
            "object": "block",
            "type": "table_of_contents",
            "table_of_contents": {
                "color": "default"
            }
        },
        {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    ]

    # Mapeo simple de extensiones a lenguajes de Notion
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.md': 'markdown',
        '.sh': 'shell',
        '.sql': 'sql',
        '.java': 'java',
        '.cpp': 'c++',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.txt': 'plain text'
    }

    for arch in archivos:
        try:
            contenido = arch.read_text(encoding='utf-8')
        except Exception:
            # Ignorar si es binario u otro error de lectura
            continue
            
        # Limitar longitud para no romper límite de bloque de Notion (2000 chars por RichText)
        # Una página soporta bloques más largos (hasta 100 limit blocks por llamada create, pero
        # cada rich_text config_text maxLength = 2000. Rompemos el contenido en chunks si es muy grande)
        # Para simplificar y debido a dependencias externas complejas de chunking en Notion:
        if len(contenido) > 2000:
             contenido = contenido[:1950] + "\n\n... [Contenido Truncado por Límite de Notion]"

        ext = arch.suffix.lower()
        lenguaje_notion = lang_map.get(ext, "plain text")

        # Heading (Ruta Relativa)
        rel_path = str(arch.relative_to(project_dir))
        children_blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": rel_path}}]
            }
        })
        
        # Code block
        children_blocks.append({
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": contenido}}],
                "language": lenguaje_notion
            }
        })

    data = {
        "parent": { "page_id": parent_page_id },
        "properties": {
            "title": [
                {
                    "text": {
                        "content": titulo_pagina
                    }
                }
            ]
        },
        "children": children_blocks
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        res_json = response.json()
        page_url = res_json.get('url', 'URL no disponible')
        return f"✅ Proyecto sincronizado exitosamente en Notion.\nEnlace: {page_url}"
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', None)
        error_msg = str(e)
        if e.response is not None:
             try:
                 error_msg += f" - {e.response.json()}"
             except Exception:
                 pass
        return f"❌ Error al publicar en Notion (Código {status_code}): {error_msg}"


def publicar_en_notion(titulo_pagina: str, contenido_markdown: str) -> str:
    """
    Crea una página simple en Notion a partir de texto estructurado en Markdown (útil para resúmenes web o notas rápidas).
    Argumentos:
        titulo_pagina: Título deseado para la página de Notion.
        contenido_markdown: El resumen de texto, preferiblemente estructurado.
    """
    notion_api_key = os.getenv('NOTION_API_KEY')
    parent_page_id = os.getenv('NOTION_PARENT_PAGE_ID')

    if not notion_api_key or not parent_page_id:
        return ("⚠️ Error de Configuración de Notion: Faltan las variables de entorno "
                "'NOTION_API_KEY' o 'NOTION_PARENT_PAGE_ID'. Por favor, añádelas a tu archivo .env.")

    # Sanitizar Page ID (por si el usuario pegó la URL completa o el título-id)
    if "notion.so" in parent_page_id or "notion.site" in parent_page_id:
        parent_page_id = parent_page_id.split("/")[-1].split("?")[0].split("-")[-1]
    elif "-" in parent_page_id:
        parent_page_id = parent_page_id.split("-")[-1]

    # Convertir a formato UUID (8-4-4-4-12) si es una cadena de 32 caracteres
    if len(parent_page_id) == 32:
        parent_page_id = f"{parent_page_id[:8]}-{parent_page_id[8:12]}-{parent_page_id[12:16]}-{parent_page_id[16:20]}-{parent_page_id[20:]}"

    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {notion_api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Trocear el contenido si supera los 2000 caracteres
    if len(contenido_markdown) > 2000:
        contenido_markdown = contenido_markdown[:1950] + "\\n\\n... [Contenido truncado por límite de Notion]"

    data = {
        "parent": { "page_id": parent_page_id },
        "properties": {
            "title": [
                {
                    "text": {
                        "content": titulo_pagina
                    }
                }
            ]
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": contenido_markdown
                            }
                        }
                    ]
                }
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        res_json = response.json()
        page_url = res_json.get('url', 'URL no disponible')
        return f"✅ Nota de texto sincronizada exitosamente en Notion.\nEnlace: {page_url}"
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', None)
        error_msg = str(e)
        if e.response is not None:
             try:
                 error_msg += f" - {e.response.json()}"
             except Exception:
                 pass
        return f"❌ Error al publicar nota en Notion (Código {status_code}): {error_msg}"
