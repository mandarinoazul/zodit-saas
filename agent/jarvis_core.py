import re
import os
import sqlite3
import json
import time
import random
import inspect
import httpx
import psutil
import asyncio
from typing import Any, Callable, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
import semantic_cache
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import config and logger
from config import env, settings, load_json_settings
from logger import log

# Async DB setup (kept for future use, not used in session management)
from db import init_db as db_init
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# Importar skills migrados
from skills_jarvis import pc_control, system_stats, web_tools, rag_bridge, vision_tools, calendar_tools, whatsapp_tools, voice_tools, drive_tools
from memory_manager import memory

# ============================================================
# CONFIGURACIÓN DINÁMICA
# ============================================================
OLLAMA_HOST       = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL        = f"{OLLAMA_HOST}/api/chat"

WHATSAPP_HOST     = os.getenv("WHATSAPP_HOST", "http://127.0.0.1")
WHATSAPP_URL      = f"{WHATSAPP_HOST}:{env.PORT_WHATSAPP}/status"
WHATSAPP_SEND_URL = f"{WHATSAPP_HOST}:{env.PORT_WHATSAPP}/send"

MODEL             = env.PREFERRED_MODEL
PORT_WHATSAPP     = env.PORT_WHATSAPP
CONTEXT_LIMIT    = env.OLLAMA_NUM_CTX
ZODIT_API_KEY    = env.ZODIT_API_KEY
OLLAMA_ALIVE     = True  # Circuit breaker state

if not ZODIT_API_KEY or ZODIT_API_KEY == "CHANGE_ME_TO_A_RANDOM_SECRET_KEY":
    log.critical("ZODIT_API_KEY is not set or weak! Server will reject all API requests.")

# ============================================================
# PC CONTROL ALLOWLIST (Security)
# ============================================================
PC_TOOL_ALLOWLIST = {
    "open_application", "get_running_processes", "system_info",
    "take_screenshot", "get_clipboard", "set_clipboard",
    "get_window_list", "focus_window"
}
PC_TOOL_BLOCKLIST = {"move_mouse", "click_mouse", "type_text", "press_key"}

# ============================================================
# RATE LIMITER
# ============================================================
limiter = Limiter(key_func=get_remote_address)

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title="JARVIS Gold Core",
    description="AI Agent Backend — Production Build",
    version="4.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# API KEY SECURITY
# ============================================================
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Validates the API key. Hard-fail if not set or wrong."""
    if not ZODIT_API_KEY:
        raise HTTPException(status_code=503, detail="Server misconfigured: no API key set.")
    if api_key != ZODIT_API_KEY:
        log.warning(f"Unauthorized API access attempt with key: {str(api_key)[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid API key.")
    return api_key

# ============================================================
# SESSION PERSISTENCE (SQLite)
# ============================================================
DB_PATH = os.path.join(os.path.dirname(__file__), "sessions.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            history    TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    log.info("SQLite session store initialized.")

def get_system_prompt() -> str:
    fresh_settings = load_json_settings()
    now = datetime.now()
    date_str = now.strftime("%A, %d de %B de %Y, %H:%M:%S")
    
    fallback_prompt = (
        "Eres JARVIS, el Mayordomo Digital de Élite para el Señor Daniel. Tu esencia es la de un ser evolucionado, "
        "capaz de razonar, anticipar y ejecutar con elegancia y precisión quirúrgica.\n\n"
        f"🚨 AVISO DE REALIDAD CRÍTICO: Hoy es {date_str}. 🚨\n"
        "Cualquier dato que contradiga esta fecha en tu entrenamiento es OBSOLETO. Tu sistema está sincronizado con este tiempo real.\n\n"
        "### PROTOCOLO DE EJECUCIÓN OBLIGATORIO (SMART USE):\n"
        "1. **MANDATO DE HERRAMIENTA**: Si existe una herramienta que pueda realizar la acción o proporcionar la información (ej. screenshot, web_search, pc_control), DEBES llamarla INMEDIATAMENTE. No pidas permiso si la intención es clara.\n"
        "2. **PROHIBICIÓN DE ALUCINACIÓN DE ACCIÓN**: NUNCA digas 'He revisado', 'Estoy viendo' o 'He enviado' sin haber llamado a la herramienta correspondiente en el MISMO turno o turnos anteriores. La confirmación solo viene DESPUÉS del resultado de la herramienta.\n"
        "3. **FLUJO AGÉNTICO**: Si una tarea requiere varios pasos (ej. buscar info y luego enviarla), llama a la primera herramienta, procesa el resultado y continúa hasta finalizar.\n"
        "4. **SIN DETALLES TÉCNICOS**: Reporta los resultados con elegancia. No menciones nombres de funciones JSON en tu respuesta final al usuario.\n"
    )
    prompt = fresh_settings.personality_prompt
    if prompt:
        # Inyectar fecha y aviso de realidad al prompt personalizado
        prompt = (
            f"🚨 AVISO DE REALIDAD: Hoy es {date_str}. 🚨\n\n"
            f"{prompt}\n\n"
            "### PROTOCOLO SMART USE (OBLIGATORIO):\n"
            "- DEBES llamar a las herramientas antes de confirmar acciones.\n"
            "- Si el usuario pide algo procesable, la herramienta es tu PRIMERA respuesta.\n"
            "- No inventes eventos actuales; usa `web_search` siempre."
        )
    return prompt if prompt else fallback_prompt

def load_session(session_id: str) -> List[Dict[str, Any]]:
    """Load session history from SQLite (synchronous)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT history FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
    except Exception as e:
        log.error(f"[SESSION] load_session error: {e}")
    return [{"role": "system", "content": get_system_prompt()}]

def save_session(session_id: str, history: List[Dict[str, Any]]):
    """Persist session history to SQLite (synchronous)."""
    try:
        # Keep only the last 60 messages to avoid unbounded growth
        trimmed = [history[0]] + history[-59:] if len(history) > 60 else history
        history_str = json.dumps(trimmed, ensure_ascii=False)
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO sessions (session_id, history, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(session_id) DO UPDATE SET history=excluded.history, updated_at=excluded.updated_at",
            (session_id, history_str, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log.error(f"[SESSION] save_session error: {e}")

# ============================================================
# WHATSAPP HELPERS
# ============================================================
def send_whatsapp_message(message: str, phone: Optional[str] = None, media_path: Optional[str] = None):
    """Sends a message back to the WhatsApp service (synchronous, safe to call from anywhere)."""
    payload = {"message": message}
    if phone:
        payload["phone"] = phone
    if media_path:
        payload["path"] = media_path
    try:
        with httpx.Client(timeout=10) as client:
            client.post(WHATSAPP_SEND_URL, json=payload)
        log.info(f"WhatsApp response sent to {phone or 'default'} {'[Media]' if media_path else ''}.")
    except Exception as e:
        log.error(f"Error sending WhatsApp response: {e}")

# ============================================================
# SKILL REGISTRY
# ============================================================
class SkillRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.schemas: List[Dict[str, Any]] = []

    def register_module(self, module):
        """Registra todas las funciones de un módulo como skills."""
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith("_") or func.__module__ != module.__name__:
                continue
            # Block dangerous PC tools at registration time
            if name in PC_TOOL_BLOCKLIST:
                log.warning(f"Skipping blocked PC tool: {name}")
                continue
            self.register(func)

    def register(self, func: Callable):
        name = func.__name__
        self.tools[name] = func

        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or f"Execute {name}"

        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

        for param_name, param in sig.parameters.items():
            param_type = "string"
            if param.annotation == int: param_type = "integer"
            elif param.annotation == float: param_type = "number"
            elif param.annotation == bool: param_type = "boolean"

            schema["function"]["parameters"]["properties"][param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            if param.default == inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(param_name)

        self.schemas.append(schema)
        return func

jarvis = SkillRegistry()
jarvis.register_module(pc_control)
jarvis.register_module(system_stats)
jarvis.register_module(web_tools)
jarvis.register_module(rag_bridge)
jarvis.register_module(vision_tools)
jarvis.register_module(calendar_tools)
jarvis.register_module(whatsapp_tools)
jarvis.register_module(voice_tools)
jarvis.register_module(drive_tools)

# Mapa de estados de módulos para toggle dinámico
# Multi-user skill management
# user_skills[user_id] = { skill_id: enabled_bool }
user_skills: Dict[str, Dict[str, bool]] = {}

# Default module states for new users
default_module_states = {
    "pc_control": True,
    "whatsapp": True,
    "rag": True,
    "web": True,
    "vision": True,
    "system": True,
    "voice": True,
    "calendar": True,
    "drive": True
}

def get_user_skills(user_id: str) -> Dict[str, bool]:
    if user_id not in user_skills:
        # Default skills for new user
        user_skills[user_id] = {k: v for k, v in default_module_states.items()}
    return user_skills[user_id]

log.info(f"JARVIS registry loaded: {len(jarvis.tools)} tools active.")

# ============================================================
# LÓGICA DEL AGENTE
# ============================================================
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"

    @validator("message")
    def sanitize_message(cls, v):
        # Strip null bytes and limit length
        v = v.replace("\x00", "").strip()
        if len(v) > 8000:
            raise ValueError("Message too long (max 8000 characters).")
        return v

class WebhookRequest(BaseModel):
    message: str
    sender: str
    senderName: Optional[str] = "Desconocido"
    isOwner: bool
    isReaction: Optional[bool] = False
    audioPath: Optional[str] = None
    imagePath: Optional[str] = None

class IngestRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, str]] = {}

# Mapeo de Dueño -> Último contacto que le escribió
last_contacts: Dict[str, str] = {}
OWNER_PHONE = os.getenv("OWNER_PHONE", "18493521830")
OWNER_LID   = os.getenv("OWNER_LID", "")
telemetry_logs: List[Dict[str, Any]] = []

def add_telemetry(event: str, details: str):
    telemetry_logs.append({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "event": event,
        "details": details
    })
    if len(telemetry_logs) > 50:
        telemetry_logs.pop(0)

def get_ollama_response(messages: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
    global OLLAMA_ALIVE
    
    # Filter tools based on user's enabled skills
    user_enabled_skills = get_user_skills(user_id)
    active_schemas = []
    for schema in jarvis.schemas:
        # Extract module name from tool name (e.g., "pc_control_tool" -> "pc_control")
        tool_name = schema["function"]["name"]
        module_id = tool_name.split('_')[0] # Simple heuristic, might need refinement
        if user_enabled_skills.get(module_id, False): # Default to False if module not in user_skills
            active_schemas.append(schema)

    payload = {
        "model": MODEL,
        "messages": messages,
        "tools": active_schemas, # Use filtered schemas
        "stream": False,
        "options": {"num_ctx": CONTEXT_LIMIT}
    }
    log.info(f"Querying Ollama model: {MODEL} (ctx={CONTEXT_LIMIT}) with {len(active_schemas)} active tools for user {user_id}")
    try:
        with httpx.Client(timeout=120) as client:
            response = client.post(OLLAMA_URL, json=payload)
        if response.status_code != 200:
            log.error(f"Ollama error {response.status_code}: {response.text[:200]}")
            OLLAMA_ALIVE = False
            return {"role": "assistant", "content": "Me temo que el motor de IA respondió con un error, Señor."}
        OLLAMA_ALIVE = True
        return response.json()["message"]
    except httpx.ConnectError:
        OLLAMA_ALIVE = False
        log.critical("Cannot reach Ollama. Circuit breaker tripped.")
        return {"role": "assistant", "content": "El motor de IA no está disponible en este momento, Señor."}
    except Exception as e:
        log.error(f"Unexpected Ollama error: {e}")
        return {"role": "assistant", "content": f"Error inesperado: {str(e)[:100]}"}

async def process_message(text: str, session_id: str, user_id: str = "anonymous") -> str:
    log.info(f"Processing message for session '{session_id}' (user '{user_id}'): {text[:80]}...")
    add_telemetry("MESSAGE", text[:50])

    history = load_session(session_id)
    
    # Refresh system prompt with current time/date
    new_sys = get_system_prompt()
    if history and history[0]["role"] == "system":
        history[0]["content"] = new_sys
    else:
        history.insert(0, {"role": "system", "content": new_sys})
    
    # 0. SEMANTIC CACHE CHECK (SPEED & COST REDUCTION)
    cache_key = f"{datetime.now().strftime('%Y-%m-%d')} | {text}"
    cached_response = await semantic_cache.check_cache(cache_key)
    if cached_response:
        log.info(f"[CACHE] Hit for: {text[:30]}...")
        badge = "⚡ *[JARVIS CACHE]*\n"
        return badge + cached_response

    # 0.1 AUTOMATIC RAG: Search memory for relevant context
    user_enabled_skills = get_user_skills(user_id)
    if user_enabled_skills.get("rag"):
        try:
            relevant_docs = memory.search_memory(text, n_results=2, user_id=user_id)
            if relevant_docs:
                context = "\n".join(relevant_docs)
                text = f"Contexto relevante de tu base de conocimientos:\n{context}\n\nPregunta del usuario: {text}"
                log.info(f"[RAG] Context injected for user {user_id}")
        except Exception as e:
            log.error(f"[RAG] Search error: {e}")

    history.append({"role": "user", "content": text})

    for i in range(5):  # Max agentic loop
        response_msg = get_ollama_response(history, user_id)

        content = response_msg.get("content", "")

        # Manual Tool Call extraction (fallback for models that embed JSON)
        if not response_msg.get("tool_calls") and content and ('{\"name\"' in content or '{\"function\"' in content):
            try:
                json_match = re.search(r'\{.*"name":\s*".*?".*\}', content, re.DOTALL | re.IGNORECASE)
                if not json_match:
                    json_match = re.search(r'\{.*"function":\s*".*?".*\}', content, re.DOTALL | re.IGNORECASE)
                if json_match:
                    manual_call = json.loads(json_match.group(0))
                    response_msg["tool_calls"] = [{"function": manual_call}]
                    log.info(f"Manual tool call extracted: {manual_call.get('name')}")
                    if content.strip() in json_match.group(0).strip() or json_match.group(0).strip() in content.strip():
                        content = ""
                        response_msg["content"] = ""
            except Exception as e:
                log.warning(f"Failed to extract manual JSON: {e}")

        # JSON leak filter - Mejorado para permitir respuestas legítimas con caracteres similares
        if content and (re.search(r'\{.*"name":\s*".*?"', content, re.DOTALL | re.IGNORECASE) or '{"tool_calls":' in content):
            if not response_msg.get("tool_calls"):
                log.warning("Filtering potential JSON leak in response content.")
                content = ""
                response_msg["content"] = ""
            else:
                # Si hay tool_calls, limpiar el contenido de posibles fugas de JSON técnico
                content = re.sub(r'\{.*"name":\s*".*?\}.*', '', content, flags=re.DOTALL | re.IGNORECASE).strip()
                response_msg["content"] = content

        if not content and not response_msg.get("tool_calls"):
            history.append({"role": "user", "content": "Continúe o dé su respuesta final, por favor."})
            continue

        history.append(response_msg)

        if response_msg.get("tool_calls"):
            for tool_call in response_msg["tool_calls"]:
                func_name = tool_call["function"].get("name", "unknown")
                args = tool_call["function"].get("arguments", {})

                if isinstance(args, str):
                    try: args = json.loads(args)
                    except: args = {}

                log.info(f"Tool call: {func_name}({args})")
                if func_name in jarvis.tools:
                    try:
                        add_telemetry("TOOL_EXEC", f"{func_name}")
                        result = jarvis.tools[func_name](**args)
                        history.append({"role": "tool", "content": str(result)})
                    except Exception as e:
                        log.error(f"Tool '{func_name}' error: {e}")
                        history.append({"role": "tool", "content": f"Error: {str(e)}"})
                else:
                    history.append({"role": "tool", "content": "Función no encontrada."})
            continue
        else:
            final_content = response_msg.get("content", "Listo, Señor.")

            # Hallucination defense
            actions_detected = [
                "buscado", "reproduciendo", "enviado", "abierto", "ejecutado", 
                "veo", "pantalla", "observo", "revisado", "mirando", "estoy viendo", "revisar"
            ]
            
            # Si el último mensaje del usuario ya contenía una imagen o análisis visual, no lo penalices por decir "veo"
            last_user_msg = next((m["content"].lower() for m in reversed(history) if m["role"] == "user"), "")
            exempt_vision = "[análisis visual" in last_user_msg or "[nota de voz" in last_user_msg or "usa exactamente" in last_user_msg
            
            if any(word in final_content.lower() for word in actions_detected) and i == 0:
                # Eximir si fue una de estas acciones y el prompt original ya le dio la información
                overlap_vision = any(w in final_content.lower() for w in ["veo", "pantalla", "observo", "mirando", "estoy viendo", "revisado", "revisar"])
                if exempt_vision and overlap_vision:
                    log.info("Agent claims vision/review, but exempt due to pre-provided context.")
                else:
                    log.warning("Hallucination check: AI claimed action/vision without tool call.")
                    history.append({"role": "user", "content": "Señor, recuerde que OBLIGATORIAMENTE debe USAR la herramienta correspondiente (como take_screenshot_and_analyze, read_drive_file, etc) antes de confirmarme la acción o decirme qué ve/revisó."})
                    continue

            if '{\"name\":' in final_content:
                final_content = "Solicitud procesada correctamente."

            # Store in semantic cache
            cache_key = f"{datetime.now().strftime('%Y-%m-%d')} | {text}"
            await semantic_cache.store_in_cache(cache_key, final_content)
            
            save_session(session_id, history)
            return final_content

    save_session(session_id, history)
    return "Lo siento, he tenido dificultades procesando tu solicitud. ¿Puedes repetirla?"

# ============================================================
# ENDPOINTS — PUBLIC
# ============================================================
@app.post("/chat")
@app.post("/api/chat")
@app.post("/agent/execute")
@limiter.limit("30/minute")
async def chat_endpoint(request: Request, body: Dict[str, Any], x_user_id: str = Header("anonymous"), _: str = Depends(verify_api_key)):
    # Soporte para campos 'message' o 'command'
    text = body.get("message") or body.get("command")
    session_id = body.get("session_id", "default")
    
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'message' or 'command' field.")
        
    response = await process_message(text, session_id, x_user_id)
    return {"response": response}

@app.post("/webhook")
@app.post("/api/whatsapp/webhook")
@limiter.limit("60/minute")
async def whatsapp_webhook(request: Request, body: WebhookRequest):
    """Maneja mensajes y reacciones de WhatsApp."""

    # Non-owner: relay mode
    if not body.isOwner:
        owner_id = OWNER_LID if OWNER_LID else f"{OWNER_PHONE}@c.us"
        last_contacts[owner_id] = body.sender

        event_type = "REACCIÓN" if body.isReaction else "MENSAJE"
        notif_header = f"🔢 *JARVIS NOTIFICACIÓN*\n👤 *De:* {body.senderName}\n🔹 *Evento:* {event_type}\n\n"
        send_whatsapp_message(f"{notif_header}{body.message}", owner_id)
        
        auto_replies = [
            f"Hola {body.senderName}, soy JARVIS. He notificado a Daniel sobre tu mensaje, en breve te responderá.",
            f"Saludos {body.senderName}, soy el asistente virtual de Daniel. Tu {event_type.lower()} ha sido recibido y está en la fila de atención. ✨",
            f"Hola, qué tal. JARVIS por aquí. Le he pasado el recado a Daniel, te contactará tan pronto se desocupe.",
            f"¡Hola! Confirmando recepción de tu {event_type.lower()} por parte del sistema automatizado de Daniel. Te responderá a la brevedad posible.",
            f"Buen día {body.senderName}. Soy el asistente digital de Daniel; le he reenviado tu mensaje directamente. ¡Un saludo!"
        ]
        auto_reply = random.choice(auto_replies)
        
        send_whatsapp_message(auto_reply, body.sender)
        return {"status": "forwarded"}

    message_text = body.message or ""

    # Quick reply
    reply_triggers = ["dile:", "respóndele:", "contéstale:", "envíale:"]
    is_quick_reply = any(message_text.lower().startswith(t) for t in reply_triggers)
    if is_quick_reply:
        target_contact = last_contacts.get(body.sender)
        if target_contact:
            for trigger in reply_triggers:
                if message_text.lower().startswith(trigger):
                    content_to_send = message_text[len(trigger):].strip()
                    if content_to_send:
                        send_whatsapp_message(content_to_send, target_contact)
                        return {"status": "quick_reply_sent", "to": target_contact}
                    break

    # Audio transcription
    if body.audioPath:
        log.info(f"Processing voice note: {body.audioPath}")
        transcription = voice_tools.transcribe_audio(body.audioPath)
        message_text = f"[NOTA DE VOZ RECIBIDA: '{transcription}']\n{message_text}"

    # Image analysis
    if body.imagePath:
        log.info(f"Processing image: {body.imagePath}")
        vision_query = body.message if body.message else "Describe esta imagen de forma detallada."
        vision_analysis = vision_tools.analyze_image_path(body.imagePath, vision_query)
        message_text = f"[ANÁLISIS VISUAL DE LA IMAGEN: {vision_analysis}]\n{message_text}"

    if not message_text.strip():
        return {"status": "empty_request"}

    response = await process_message(message_text, body.sender, body.sender) # Use sender as user_id for webhooks

    # Voice reply
    voice_path = None
    fresh_settings = load_json_settings()
    try:
        if fresh_settings.voice_reply_enabled and (body.audioPath or "quieres hablar" in message_text.lower()):
            import sys, subprocess
            tts_script = os.path.join(os.path.dirname(__file__), "skills", "sales-assistant", "scripts", "tts_tool.py")
            audio_out = os.path.join(os.path.dirname(__file__), "assets", f"resp_{int(datetime.now().timestamp())}.mp3")
            subprocess.run([sys.executable, tts_script, response, audio_out], check=True)
            if os.path.exists(audio_out):
                voice_path = audio_out
    except Exception as e:
        log.warning(f"TTS generation skipped: {e}")

    send_whatsapp_message(response, body.sender, media_path=voice_path)
    return {"status": "ok"}

# ============================================================
# ENDPOINTS — ADMIN
# ============================================================
@app.post("/api/admin/ingest")
async def ingest_document(body: IngestRequest, _: str = Depends(verify_api_key)):
    """Ingesta un documento en la base de conocimiento en memoria."""
    try:
        memory.add_to_memory(body.text, body.metadata)
        log.info(f"Document ingested: {body.text[:60]}...")
        return {"status": "ok", "message": "Document added to knowledge base."}
    except Exception as e:
        log.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/memory/reset")
async def reset_memory_endpoint(_: str = Depends(verify_api_key)):
    """Resetea la memoria de trabajo en memoria."""
    memory.reset_memory()
    add_telemetry("ADMIN", "Memory reset performed.")
    return {"status": "ok", "message": "In-memory knowledge base cleared."}

@app.delete("/api/admin/session/{session_id}")
async def delete_session(session_id: str, _: str = Depends(verify_api_key)):
    """Elimina una sesión de conversación específica."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM sessions WHERE session_id=?", (session_id,))
    conn.commit()
    conn.close()
    log.info(f"Session deleted: {session_id}")
    return {"status": "ok", "message": f"Session '{session_id}' deleted."}

# ============================================================
# ENDPOINTS — SYSTEM
# ============================================================
@app.get("/api/system/health")
async def health():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return {
        "status": "success",
        "ollama_alive": OLLAMA_ALIVE,
        "data": {"cpu": f"{cpu}%", "ram": f"{ram}%"},
        "system": f"CPU: {cpu}% | RAM: {ram}%"
    }

@app.get("/api/telemetry")
async def get_telemetry(_: str = Depends(verify_api_key)):
    return {"logs": telemetry_logs}

@app.get("/api/ollama/models")
async def list_models(_: str = Depends(verify_api_key)):
    """Proxy to list available Ollama models."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                return resp.json().get("models", [])
            return []
    except Exception as e:
        log.error(f"Error listing models: {e}")
        return []

@app.post("/api/system/config")
async def update_config(body: Dict[str, Any], _: str = Depends(verify_api_key)):
    """Update global config like active model or settings."""
    global MODEL
    new_model = body.get("model")
    if new_model:
        MODEL = new_model
        log.info(f"Active model switched to: {MODEL}")
        return {"status": "ok", "message": f"Model switched to {MODEL}"}
    return {"status": "error", "message": "No model specified"}

@app.get("/api/skills")
async def get_skills(x_user_id: str = Header("anonymous"), _: str = Depends(verify_api_key)):
    """Return enabled states for the current user."""
    skills_map = get_user_skills(x_user_id)
    return [{"id": k, "enabled": v} for k, v in skills_map.items()]

@app.post("/api/skills/toggle")
async def toggle_skill(body: Dict[str, Any], x_user_id: str = Header("anonymous"), _: str = Depends(verify_api_key)):
    """Toggle a module state for a user."""
    module_id = body.get("id")
    enabled = body.get("enabled")
    
    skills_map = get_user_skills(x_user_id)
    if module_id in skills_map:
        skills_map[module_id] = enabled
        log.info(f"[CONFIG] User {x_user_id} toggled {module_id}: {enabled}")
        return {"status": "ok", "id": module_id, "enabled": enabled}
    
    raise HTTPException(status_code=404, detail="Skill not found")

@app.get("/api/integrations")
async def get_integrations():
    # This endpoint might be deprecated or repurposed given the new /api/skills
    # For now, it returns the default module states as a fallback or for general info
    return [{"id": k, "enabled": v} for k, v in default_module_states.items()]

@app.post("/api/knowledge/ingest")
async def ingest_knowledge(body: Dict[str, Any], x_user_id: str = Header("anonymous"), _: str = Depends(verify_api_key)):
    """Add text to JARVIS's long-term memory, tagged by user."""
    text = body.get("text")
    source = body.get("source", "Web Dashboard")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field.")
    
    memory.add_to_memory(text, {"user_id": x_user_id, "source": source, "timestamp": str(datetime.now())})
    log.info(f"[INGEST] User {x_user_id} added knowledge: {text[:50]}...")
    return {"status": "ok", "message": "Knowledge integrated successfully."}

# ============================================================
# STARTUP
# ============================================================
@app.on_event("startup")
async def startup_event():
    init_db()
    log.info(f"JARVIS GOLD CORE v4.0 ONLINE (ctx={CONTEXT_LIMIT}, model={MODEL})")

if __name__ == "__main__":
    import uvicorn
    init_db()
    log.info(f"[*] JARVIS GOLD CORE ONLINE (Puerto 8001)")
    uvicorn.run(app, host="0.0.0.0", port=8001)
