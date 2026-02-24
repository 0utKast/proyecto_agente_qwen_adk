import sqlite3
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import settings

class MemoryManager:
    def __init__(self, db_path: str = settings.MEMORIA_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    history_json TEXT,
                    summary TEXT,
                    last_updated REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    metadata_json TEXT,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query TEXT PRIMARY KEY,
                    result_summary TEXT,
                    timestamp REAL
                )
            """)

    def save_session(self, session_id: str, history: List[Dict[str, Any]], summary: Optional[str] = None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO sessions (session_id, history_json, summary, last_updated)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    history_json=excluded.history_json,
                    summary=COALESCE(excluded.summary, sessions.summary),
                    last_updated=excluded.last_updated
            """, (session_id, json.dumps(history), summary, time.time()))

    def get_session(self, session_id: str) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT history_json, summary FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            if row:
                return {"history": json.loads(row[0]), "summary": row[1]}
            return {"history": [], "summary": None}

    def save_search(self, query: str, result: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO search_cache (query, result_summary, timestamp)
                VALUES (?, ?, ?)
                ON CONFLICT(query) DO UPDATE SET
                    result_summary=excluded.result_summary,
                    timestamp=excluded.timestamp
            """, (query, result, time.time()))

    def get_cached_search(self, query: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT result_summary FROM search_cache WHERE query = ?", (query,)).fetchone()
            if row:
                return row[0]
            return None

    def search_past_memories(self, search_term: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            results = []
            search_term_clean = search_term.lower().strip()
            # Dividir en palabras para búsquedas más amplias si es una frase
            words = [w for w in search_term_clean.split() if len(w) > 3]
            
            # 1. Buscar en resúmenes
            rows = conn.execute("SELECT session_id, summary FROM sessions WHERE summary LIKE ? LIMIT 5", (f"%{search_term_clean}%",)).fetchall()
            for row in rows:
                if row[1]:
                    results.append(f"--- SESIÓN {row[0]} (Resumen) ---\n{row[1]}")
            
            # 2. Buscar en el historial crudo
            if len(results) < 5:
                # Buscar por el término completo o por palabras clave importantes
                query = "SELECT session_id, history_json FROM sessions WHERE history_json LIKE ? "
                params = [f"%{search_term_clean}%"]
                
                for w in words[:2]: # No abusar de ORs
                    query += "OR history_json LIKE ? "
                    params.append(f"%{w}%")
                
                query += "ORDER BY last_updated DESC LIMIT 10"
                
                rows = conn.execute(query, tuple(params)).fetchall()
                for row in rows:
                    if len(results) >= 10: break
                    history = json.loads(row[1])
                    
                    found_in_session = []
                    for i, msg in enumerate(history):
                        content_low = msg["content"].lower()
                        if search_term_clean in content_low or any(w in content_low for w in words):
                            found_in_session.append(f"[{msg['role'].upper()}]: {msg['content'][:300]}...")
                            if msg['role'] == 'user' and i + 1 < len(history):
                                next_msg = history[i+1]
                                if next_msg['role'] == 'agent':
                                    found_in_session.append(f"[AGENTE (Respuesta)]: {next_msg['content'][:500]}...")
                            break
                    
                    if found_in_session:
                        results.append(f"--- SESIÓN {row[0]} (Historial) ---\n" + "\n".join(found_in_session))
            
            # 3. Caché de búsquedas web
            if len(results) < 10:
                rows = conn.execute("SELECT query, result_summary FROM search_cache WHERE query LIKE ? OR result_summary LIKE ? LIMIT 3", 
                                   (f"%{search_term_clean}%", f"%{search_term_clean}%")).fetchall()
                for row in rows:
                    results.append(f"--- BÚSQUEDA WEB PREVIA: '{row[0]}' ---\n{row[1][:400]}...")
                
            return "\n\n".join(results) if results else f"No se encontraron recuerdos sobre '{search_term}'. Pide al usuario que te refresque la memoria o intenta otros términos."

memory_manager = MemoryManager()
