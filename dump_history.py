import sqlite3
import json
from pathlib import Path

db_path = Path("/Volumes/MisAppsV/Google _ADK/agents/qwen_arquitecto/agente_memoria.db")

if not db_path.exists():
    print(f"Database not found at {db_path}")
else:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id, history_json FROM sessions ORDER BY last_updated DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            session_id, history_json = row
            print(f"--- LATEST SESSION: {session_id} ---")
            history = json.loads(history_json)
            # Only print the last 15 messages to not overwhelm output
            for msg in history[-15:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                print(f"\n[{role.upper()}]:\n{content[:500]}..." if len(content) > 500 else f"\n[{role.upper()}]:\n{content}")
        else:
            print("No sessions found in the database.")
