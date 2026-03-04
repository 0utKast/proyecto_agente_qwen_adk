# Proyecto Agente Qwen ADK 🤖🚀 (v1.1.0)

Bienvenido al repositorio oficial del **Proyecto Agente Qwen ADK**, un sistema avanzado de **Orquestación Multi-Agente 100% Local** construido sobre el Google Agent Development Kit (ADK) y potenciado por modelos de lenguaje de código abierto a través de Ollama (específicamente la familia Qwen3).

---

## 🌟 Características Principales

*   **Arquitectura Jerárquica Multi-Agente:**
    *   **Qwen Architect (Manager):** El orquestador principal. Piensa, planifica, delega tareas y consolida resultados.
    *   **Researcher-Bot:** Especialista en extraer y sintetizar información técnica de internet.
    *   **Coder:** Desarrollador puro, enfocado exclusivamente en generar código limpio, seguro y funcional.
    *   **Quality-Bot:** Auditor de seguridad y calidad del código.
*   **Integración Oficial con WhatsApp (Novedad v1.1):** 📲
    *   Conexión segura vía **Twilio WhatsApp Sandbox** (sin riesgo de baneo).
    *   **Soporte Multi-Agente**: Cambia de bot directamente desde el chat usando comandos (ej. `/agent coder`).
    *   Historial de conversación persistente e individual por número de teléfono.
*   **Ejecución 100% Local y Privada:** Todo el razonamiento ocurre en tu propia máquina usando Ollama. Sin fugas de datos de código a la nube.
*   **Gestión Robusta de Contexto (Memoria a Largo Plazo):**
    *   Persistencia de sesiones en bases de datos SQLite local.
    *   Resúmenes semánticos automáticos para no saturar la ventana de tokens.
*   **Workspace Sandboxizado:** El agente opera dentro de un directorio controlado (`Agente_Workspace`), protegiendo tu sistema.
*   **Organización Inteligente de Artefactos:** Los archivos generados se guardan automáticamente en subcarpetas semánticas por sesión.

---

## 🛠️ Requisitos Previos

1.  **Hardware Compatible:** Mac con Apple Silicon (M1/M2/M3/M4) recomendado, o PC con suficiente VRAM.
2.  **Ollama:** Instalado y ejecutándose con los modelos Qwen3 descargados.
3.  **Python 3.10+:** Entorno virtual recomendado.
4.  **ngrok:** Necesario para exponer el webhook local al sandbox de Twilio (vía túnel seguro).

---

## 🚀 Instalación y Configuración

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/TU-USUARIO/proyecto_agente_qwen_adk.git
    cd proyecto_agente_qwen_adk
    ```

2.  **Configurar el Entorno:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configurar Variables (.env):**
    Copia tu Account SID y Auth Token de Twilio en el archivo `.env`.
    Define también tu `NGROK_STATIC_DOMAIN` para una URL permanente.

---

## 📲 Uso de WhatsApp

Para activar el canal de WhatsApp de forma rápida:

1.  Asegúrate de tener **Ollama** abierto.
2.  **Doble clic** en `Lanza_WhatsApp.command` (en el escritorio o raíz del proyecto).
3.  Escribe a tu número de **Twilio Sandbox** desde WhatsApp.

### Comandos en el Chat:
- `/agent coder`: Cambia a modo programador.
- `/agent researcher-bot`: Activa la búsqueda web.
- `/status`: Mira qué agente está activo.
- `/help`: Lista completa de comandos.

---

## 📁 Estructura del Proyecto

*   `agents/qwen_arquitecto/`: Lógica central del agente (ADK).
*   `whatsapp_bridge/`: Servidor FastAPI que conecta Twilio con el agente local.
*   `start_whatsapp.py`: Script de automatización (ngrok + bridge + webhook update).
*   `Lanza_WhatsApp.command`: Acceso directo para macOS.
*   `Agente_Workspace/`: Directorio donde el agente realiza sus operaciones de archivos.

---

## 🎓 Uso Académico

Este proyecto demuestra la viabilidad de interfaces de mensajería para agentes locales, manteniendo la privacidad de los datos pero permitiendo una interacción fluida y ubicua a través de plataformas oficiales como WhatsApp.

---
*Desarrollado como proyecto final de curso sobre Orquestación de Agentes con Modelos Locales.*
