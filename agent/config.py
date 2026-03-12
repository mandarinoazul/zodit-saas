import os
import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings

# Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
SETTINGS_JSON_PATH = BASE_DIR / "assets" / "settings_gold.json"

class AppSettings(BaseModel):
    """Loaded from settings_gold.json"""
    agent_name: str = "Zodit Gold"
    personality_prompt: str = ""
    model_name: str = "llama3.1:8b"
    vision_model: str = "llama3.2-vision:latest"
    transcription_model: str = "small"
    require_confirmation: bool = True
    history_limit: int = 10
    temperature: float = 0.5
    top_p: float = 0.8
    whisper_prompt: str = ""
    enabled_tools: list[str] = []
    voice_reply_enabled: bool = False

class EnvSettings(BaseSettings):
    """Loaded from .env file"""
    PORT_GATEWAY: int = 5000
    PORT_TOOLS: int = 5005
    PORT_WHATSAPP: int = 3001
    
    ZODIT_API_KEY: str = Field(..., description="API Key for internal Gateway communication")
    DASHBOARD_SECRET: str = Field(default="secret", description="Dashboard session secret")
    DASHBOARD_PASS: str = Field(default="admin", description="Dashboard login password")
    
    USER_NAME: str = "Usuario"
    OWNER_PHONE: str = ""
    RAG_DRIVE_PATH: str = ""
    PREFERRED_MODEL: str = "llama3.1:8b"
    VISION_MODEL: str = "llama3.2-vision:latest"
    OLLAMA_NUM_CTX: int = 32768
    RAG_IN_MEMORY: bool = True

    model_config = ConfigDict(env_file=str(ENV_PATH), env_file_encoding='utf-8', extra='ignore')

def load_json_settings() -> AppSettings:
    """Load settings from assets/settings_gold.json"""
    if SETTINGS_JSON_PATH.exists():
        with open(SETTINGS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AppSettings(**data)
    return AppSettings()

# Lazy-loaded globals to be accessed by other modules
env = EnvSettings()
settings = load_json_settings()

if __name__ == "__main__":
    print(f"✅ Config loaded correctly. API KEY prefix: {env.ZODIT_API_KEY[:5]}...")
    print(f"✅ Settings loaded from JSON: Agent Name = {settings.agent_name}")
