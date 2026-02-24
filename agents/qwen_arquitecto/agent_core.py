import os
import asyncio
from typing import List, Dict, Any, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.function_tool import FunctionTool
from google.adk.sessions.session import Session
from google.adk.events.event import Event
from google.genai import types
from .config import settings
from .tools import TOOLS, current_session_var

# Configuración de LiteLlm para Ollama
# El modelo debe tener el prefijo ollama/ o ollama_chat/
# Usamos ollama_chat/ para mejor compatibilidad con streaming y herramientas
ollama_model = LiteLlm(
    model=f"ollama_chat/{settings.CODER_MODEL.split('/')[-1]}",
    base_url=settings.OLLAMA_BASE_URL,
    completion_args={
        "num_ctx": 8192,  # Reducido de 32768 a 8192 para evitar Timeouts de Ollama en modelos de 30B
        "max_tokens": 4096, # Ajustado para mantener la proporción
        "timeout": 600,   # Asegurarse de que LiteLLM no corte de forma prematura
    }
)

import sqlite3
import json

class SessionMemory:
    """
    Sistema de persistencia de sesiones en SQLite para Google ADK.
    """
    def __init__(self, db_path: str = settings.SESSION_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_history (
                    session_id TEXT PRIMARY KEY,
                    history_json TEXT
                )
            """)

    def load_session(self, session_id: str, adk_session: Session):
        """Carga el historial guardado en la sesión de ADK."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT history_json FROM session_history WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                history = json.loads(row[0])
                # Reconstruir el historial en la sesión de ADK si es necesario
                # Nota: ADK maneja su propia estructura de eventos. Aquí simplificamos 
                # guardando los intercambios básicos o los eventos serializados.
                pass

    def save_session(self, session_id: str, adk_session: Session):
        """Guarda el estado actual de la sesión."""
        # En una implementación real, serializaríamos los eventos de la sesión
        # adk_session.events
        pass

from google.adk.agents.invocation_context import InvocationContext, new_invocation_context_id
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.agents.run_config import RunConfig
from .memory_manager import memory_manager

class MockSessionService(BaseSessionService):
    def get_session(self, session_id: str) -> Session:
        return Session(id=session_id, app_name="qwen_arquitecto", user_id="local_user")
    def save_session(self, session: Session):
        pass
    def create_session(self, session: Session) -> Session:
        return session
    def delete_session(self, session_id: str):
        pass
    def list_sessions(self) -> list[Session]:
        return []

AGENT_PROFILES = {
    "arquitecto": None, # Usa el SYSTEM_INSTRUCTIONS por defecto de agent.py
    "coder": """Eres Qwen Coder, un programador experto. Tu único objetivo es generar código sólido, limpio y bien estructurado.
No uses verbosidad, ve directo a la solución. Responde únicamente con el código solicitado y unas breves instrucciones de uso si es estrictamente necesario.""",
    "quality-bot": """Eres Quality-Bot, un especialista en Quality Assurance, seguridad y rendimiento. No tienes acceso a internet.
Tu única función es recibir código o textos del Arquitecto, buscar errores lógicos, inconsistencias o vulnerabilidades de seguridad que pudieran existir y reportarlos de forma precisa y técnica. Sé directo y estructurado.""",
    "researcher-bot": """Eres Researcher-Bot, un investigador técnico analítico.
Estás optimizado exclusivamente para el uso de búsqueda web y lectura de URLs. Tu objetivo es buscar información, verificarla cruzadamente, y entregar informes técnicos brutos pero rigurosamente verificados. Usa listas, proporciona los enlaces fuente y omite introducciones o conclusiones largas."""
}

class LocalADKAgent:
    """
    Agente que utiliza Google ADK con persistencia SQLite y búsqueda web.
    """
    def __init__(self, profile: str = "arquitecto", name: Optional[str] = None):
        self.memory = memory_manager
        
        # Filtrar herramientas: Aislamiento estricto de capacidades por perfil
        filtered_tools = []
        internet_tools = ["busqueda_web", "leer_pagina_web", "extraer_resumen_web"]
        
        for t in TOOLS:
            t_name = t.__name__
            
            # Ningún sub-agente puede delegar tareas (evita bucles infinitos)
            if profile != "arquitecto" and t_name == "delegar_tarea":
                continue
                
            # Quality-Bot no tiene acceso a internet
            if profile == "quality-bot" and t_name in internet_tools:
                continue
                
            # Researcher-Bot solo tiene acceso a herramientas de internet (y quizás utilidades básicas de caché)
            # Para asegurar "uso exclusivo", lo limitamos a buscar y leer, sin tocar el sistema de archivos
            if profile == "researcher-bot" and t_name not in internet_tools:
                continue
                
            filtered_tools.append(t)
            
        adk_tools = [FunctionTool(func=t) for t in filtered_tools]
        
        from .agent import SYSTEM_INSTRUCTIONS
        
        # Seleccionar instrucciones y nombre según perfil
        if profile in AGENT_PROFILES and AGENT_PROFILES[profile]:
            instruction = AGENT_PROFILES[profile]
            agent_name = name or f"Qwen_{profile.replace('-', '_').title().replace('_', '')}"
        else:
            instruction = SYSTEM_INSTRUCTIONS
            agent_name = name or settings.AGENT_NAME
            
        self.agent = LlmAgent(
            name=agent_name,
            model=ollama_model,
            tools=adk_tools,
            instruction=instruction
        )
        self.session_service = MockSessionService()
        self.profile = profile

    async def run(self, user_input: str, session_id: str = "default_session"):
        current_session_var.set(session_id)
        session = Session(id=session_id, app_name=settings.AGENT_NAME, user_id="local_user")
        
        # 1. Recuperación automática del contexto previo
        saved_data = self.memory.get_session(session_id)
        
        # Inyectar resumen si existe
        context_input = user_input
        if saved_data["summary"]:
            context_input = f"[RESUMEN DE MEMORIA]: {saved_data['summary']}\n\n[USUARIO]: {user_input}"
            
        # Crear contenido del usuario (REQUERIDO para que el agente sepa qué hacer)
        user_content = types.Content(
            role="user",
            parts=[types.Part(text=context_input)]
        )
        
        # Crear contexto de invocación (requerido por ADK)
        ctx = InvocationContext(
            invocation_id=new_invocation_context_id(),
            agent=self.agent,
            session=session,
            session_service=self.session_service,
            run_config=RunConfig(max_llm_calls=15), # Límite de seguridad contra bucles
            user_content=user_content
        )
        
        # Registrar el evento del usuario en la sesión para persistencia
        session.events.append(Event(author="user", content=user_content, invocation_id=ctx.invocation_id))
        
        print(f"[*] Procesando petición en sesión: {session_id}")
        
        response_text = ""
        try:
            async for event in self.agent.run_async(ctx):
                # Registrar el evento en la sesión (mantiene el historial vivo)
                session.events.append(event)
                
                # Debug de eventos
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"[DEBUG ADK] Recibido texto: {repr(part.text[:50])}...")
                        elif getattr(part, "function_call", None):
                            print(f"[DEBUG ADK] Función llamada: {part.function_call.name}")
                elif getattr(event.actions, "agent_state", None) and hasattr(event.actions.agent_state, "error"):
                    print(f"[DEBUG ADK] Error del agente: {event.actions.agent_state.error}")
                                
                # En ADK, el contenido está dentro de event.content.parts
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
            elif event.actions.agent_state and hasattr(event.actions.agent_state, "error"):
                 return f"Error en el agente: {event.actions.agent_state.error}"
        except Exception as e:
            print(f"!!! [DEBUG FATAL] Error en run_async: {str(e)} !!!")
            return f"Error fatal durante inferencia: {str(e)}"
                 
        import re
        # Busca bloques como ```[ARTEFACTO: python] ... ``` o variaciones que el LLM pueda cometer
        clean_pattern = re.compile(r"```[a-zA-Z0-9\-]*\s*\[?ARTEFACTO:\s*([^\]\n]+)\]?\n?(.*?)(?:```|$)", re.DOTALL | re.IGNORECASE)
        
        def artifact_replacer(match):
            tipo = match.group(1).strip()
            return f"\n> 🛠️ **[Artefacto Excluido de Vista: {tipo}]** - \n> *El código fuente completo se ha guardado en el archivo del proyecto correspondiente.*\n"
            
        response_text = clean_pattern.sub(artifact_replacer, response_text)
        
        # 2. Lógica de Persistencia y Resumen
        # Formatear el historial para guardar en SQLite
        current_history = []
        for e in session.events:
            # Solo guardamos eventos que no sean parciales (streaming) para evitar duplicados en la DB
            if e.partial:
                continue
                
            if e.content and e.content.parts:
                text_content = "".join([p.text for p in e.content.parts if p.text])
                if text_content:
                    current_history.append({"role": e.author, "content": text_content})
                # También guardar function calls como parte del historial si fuera necesario
        
        new_summary = saved_data["summary"]
        total_chars = sum(len(h["content"]) for h in current_history)
        if total_chars > settings.SUMMARIZATION_THRESHOLD:
            # Lógica de resumen simplificada
            pass

        self.memory.save_session(session_id, current_history, summary=new_summary)
        return response_text or "El agente terminó sin una respuesta textual clara."
