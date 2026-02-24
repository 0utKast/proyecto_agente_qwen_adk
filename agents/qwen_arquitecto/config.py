import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings

def verify_env_exists():
    """Verifica si existe un archivo .env en la raíz del proyecto."""
    # Assuming that config.py is inside /agents/qwen_arquitecto/, moving three levels up reaches Google _ADK
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"
    
    if not env_path.exists():
        print(f"⚠️  [ADVERTENCIA DE SEGURIDAD] No se encontró el archivo .env en: {env_path}", file=sys.stderr)
        print("⚠️  [ADVERTENCIA DE SEGURIDAD] Asegúrate de crear el archivo .env para proteger tus API Keys y credenciales.", file=sys.stderr)

verify_env_exists()

class Settings(BaseSettings):
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Model Configuration
    # Optimized for Qwen3 Coder
    CODER_MODEL: str = "ollama/qwen3-coder"
    GENERAL_MODEL: str = "ollama/llama3.1"
    
    # ADK / Agent Configuration
    AGENT_NAME: str = "qwen_arquitecto"
    SESSION_DB_PATH: str = str(Path(__file__).parent / "sessions.db")
    MEMORIA_DB_PATH: str = str(Path(__file__).parent / "agente_memoria.db")
    SUMMARIZATION_THRESHOLD: int = 2000
    
    # Workspace Sandbox
    WORKSPACE_DIR: str = "/Users/jesusconde/Agente_Workspace"
    
    # Hardware Optimization
    GPU_LAYERS: int = 1  # Corresponds to OLLAMA_NUM_GPU

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
