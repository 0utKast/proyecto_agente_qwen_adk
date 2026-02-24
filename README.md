# Proyecto Agente Qwen ADK 🤖🚀

Bienvenido al repositorio oficial del **Proyecto Agente Qwen ADK**, un sistema avanzado de **Orquestación Multi-Agente 100% Local** construido sobre el Google Agent Development Kit (ADK) y potenciado por modelos de lenguaje de código abierto a través de Ollama (específicamente la familia Qwen3).

Este proyecto representa el pináculo de la automatización de flujos de trabajo de desarrollo de software utilizando IA local, demostrando cómo una arquitectura de agentes especializados puede superar con creces a un único LLM genérico.

---

## 🌟 Características Principales

*   **Arquitectura Jerárquica Multi-Agente:**
    *   **Qwen Architect (Manager):** El orquestador principal. Piensa, planifica, delega tareas y consolida resultados.
    *   **Researcher-Bot:** Especialista en extraer y sintetizar información técnica de internet.
    *   **Coder:** Desarrollador puro, enfocado exclusivamente en generar código limpio, seguro y funcional.
    *   **Quality-Bot:** Auditor de seguridad y calidad del código.
*   **Ejecución 100% Local y Privada:** Todo el razonamiento ocurre en tu propia máquina usando Ollama. Sin fugas de datos de código a la nube.
*   **Gestión Robusta de Contexto (Memoria a Largo Plazo):**
    *   Persistencia de sesiones en bases de datos SQLite (`agente_memoria.db`).
    *   Resúmenes semánticos automáticos para no saturar la ventana de tokens.
*   **Workspace Sandboxizado:** El agente opera dentro de un directorio controlado (`Agente_Workspace`), protegiendo tu sistema.
*   **Organización Inteligente de Artefactos:** Los archivos generados se guardan automáticamente en subcarpetas semánticas por sesión (ej. `2026-02-24_Capsula_Seguridad`), manteniendo un historial ordenado de la evolución del código.
*   **Ingeniería Anti-Bucle ("Hard-Stops"):** Mecanismos avanzados en los `System Prompts` y en los valores de retorno de las herramientas para evitar los clásicos infinitos bucles de razonamiento de los LLMs locales.
*   **Integraciones Útiles:**
    *   Extracción web profunda (limpiando ruido HTML).
    *   Sincronización con **Notion** para documentación.
    *   Gestión temporal con **Google Calendar** para agendar revisiones de código de forma inteligente (respetando huecos libres).

---

## 🛠️ Requisitos Previos

1.  **Hardware Compatible:** Mac con Apple Silicon (M1/M2/M3/M4) recomendado, o PC con suficiente VRAM para correr modelos 14B-32B fluidamente.
2.  **Ollama:** Instalado y ejecutándose. Asegúrate de tener los modelos descargados (ej. `ollama run qwen2.5-coder:14b` o similares que hayas configurado).
3.  **Python 3.10+:** Preferiblemente en un entorno virtual (`.venv`).
4.  **Google ADK:** Las dependencias necesarias para el framework de desarrollo de agentes.

## 🚀 Instalación y Configuración

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/TU-USUARIO/proyecto_agente_qwen_adk.git
    cd proyecto_agente_qwen_adk
    ```

2.  **Crear y activar el entorno virtual:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Instalar dependencias:**
    *(Asegúrate de tener un `requirements.txt` o instalar google-adk, litellm, pydantic, duckduckgo-search, beautifulsoup4, requests, etc.)*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno (.env):**
    Crea un archivo `.env` en la raíz del proyecto. Deberás configurar:
    *   `WORKSPACE_DIR`: La ruta absoluta donde el agente guardará los proyectos (ej. `/Users/tu_usuario/Agente_Workspace`).
    *   `OLLAMA_BASE_URL`: (Opcional, defecto: `http://localhost:11434`)
    *   Credenciales de la API de Notion (si usas esas herramientas).
    *   Ruta al JSON de credenciales de la cuenta de servicio de Google Calendar (si usas esa herramienta).

    *(Aviso: El archivo `.env` está en `.gitignore` por defecto para proteger tus claves en subidas futuras, pero en este commit inicial los artefactos de ejemplo podrían estar incluidos para estudio).*

---

## 🎮 Uso Básico

El núcleo del sistema reside en `agents/qwen_arquitecto/`. Para iniciar la interfaz del agente (usualmente a través del servidor UI proporcionado por ADK o un script de inicio custom):

1.  Asegúrate de que Ollama está corriendo.
2.  Inicia el agente (dependiendo de tu script principal, por ejemplo):
    ```bash
    python run_agent.py
    ```
    *(Si usas el servidor web/UI del ADK local, lanza el servidor correspondiente).*

### El Patrón "Cápsula de Seguridad" (Ejemplo de Orquestación)

Para ver el sistema brillar, puedes darle al Arquitecto un prompt complejo que active a toda la jerarquía subsidiaria:

> *"Architect, inicia el proyecto 'Cápsula de Seguridad', actuando tú solo como Orquestador. Primero, delega en el perfil `researcher-bot` la búsqueda de las mejores prácticas para prevenir ataques de Inyección SQL en Python. Una vez tengas su informe, pásale esas directrices al perfil `coder` y delégale la escritura de una función de login en Python. Finalmente, envía ese código al perfil `quality-bot` para que realice una auditoría estricta de seguridad. Cuando tengas el veredicto, recopila todo y guárdalo como un Artefacto."*

---

## 📁 Estructura del Proyecto

*   `agents/qwen_arquitecto/agent.py`: Definición principal del agente, System Prompts e inicialización.
*   `agents/qwen_arquitecto/agent_core.py`: Motor interno, instanciación de clases, gestión de perfiles e intercepción de bucles.
*   `agents/qwen_arquitecto/tools.py`: El corazón funcional. Aquí residen todas las habilidades (búsqueda web, gestión de archivos, y el crucial método `delegar_tarea`).
*   `agents/qwen_arquitecto/memory_manager.py`: Lógica de bases de datos SQLite para historial y caché.
*   `Agente_Workspace/`: (Carpeta de ejemplo) Dónde el agente guarda su trabajo ordenado por fecha y proyecto.

## 🎓 Uso Académico y Estudio

Este repositorio incluye intencionadamente ciertos archivos generados (artefactos, cachés locales de ejemplo, y logs) que habitualmente se excluirían vía `.gitignore`. Se han mantenido para que los estudiantes del curso puedan inspeccionar la estructura de carpetas final (`Proyectos_Agente`), los índices `README.md` auto-generados y los resultados crudos de las delegaciones sin tener que ejecutar todo el entorno desde cero.

---

*Desarrollado como proyecto final de curso sobre Orquestación de Agentes con Modelos Locales.*
