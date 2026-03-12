import os
import json
import urllib.request
import subprocess
import threading
import sys
import re
import base64
import asyncio
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from typing import Any, cast
from functools import wraps

from nlu_tools import detect_pc_commands, extract_phone_number, parse_send_commands
from session_manager import get_session as _base_get_session, prune_sessions as _base_prune_sessions, save_session as _base_save_session
import semantic_cache
import metrics

# Import config and logger implementation
import httpx
from config import env, load_json_settings
from logger import log

# --- IMPORTACIÓN DE HERRAMIENTAS CORE ---
SCRIPTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills", "sales-assistant", "scripts")
if SCRIPTS_PATH not in sys.path:
    sys.path.append(SCRIPTS_PATH)

try:
    import rag_tool
except ImportError:
    print(f"CRITICAL: No se pudo importar rag_tool desde {SCRIPTS_PATH}")
    # Fallback or placeholder for rag_tool if necessary
    class RagToolFallback:
        def query_knowledge(self, *args, **kwargs): return ""
        def query_memories(self, *args, **kwargs): return ""
        def add_memory(self, *args, **kwargs): pass
    rag_tool = RagToolFallback()

# =================================================================
# ZODIT GOLD v3.1 - PRO CORE GATEWAY
# PUERTO: 5000
# Nuevo: NLU Semántico, Session Context, SEND_MESSAGE regex-first
app = FastAPI(title="Zodit Gold Gateway", description="Zodit Gold v3.1 API Orchestrator", version="3.1.0")

# --- Prometheus Observability ---
app.include_router(metrics.router)

# --- MIDDLEWARE DE CORS (Opcional, si Dashboard está en otro origin) ---
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PUERTOS Y URLS DESDE CONFIG ---
PORT_GATEWAY   = env.PORT_GATEWAY
PORT_TOOLS     = env.PORT_TOOLS
PORT_WHATSAPP  = env.PORT_WHATSAPP
ZODIT_API_KEY  = env.ZODIT_API_KEY

if not ZODIT_API_KEY or ZODIT_API_KEY == "CHANGE_ME_TO_A_RANDOM_SECRET_KEY":
    log.critical("ZODIT_API_KEY no está configurada o usa un valor débil.")
    raise RuntimeError("ZODIT_API_KEY no está configurada o usa un valor débil. Configura una clave segura en el archivo .env antes de iniciar el gateway.")

TOOL_SERVER_URL   = f"http://127.0.0.1:{PORT_TOOLS}"
WHATSAPP_BASE_URL = f"http://127.0.0.1:{PORT_WHATSAPP}"

# --- RUTAS ---
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR  = os.path.join(BASE_DIR, "skills", "sales-assistant")
SCRIPTS_DIR = os.path.join(SKILLS_DIR, "scripts")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
MEMORY_FILE = os.path.join(ASSETS_DIR, "memory_gold.json")
SETTINGS_FILE = os.path.join(ASSETS_DIR, "settings_gold.json")
RAG_DRIVE_PATH = os.getenv("RAG_DRIVE_PATH", r"G:\My Drive\mi")
USER_NAME      = os.getenv("USER_NAME", "Mandev")
PYTHON_EXE     = "python"
PYTHON_ARGS    = ["python"]  # Used in safe subprocess calls

# --- AUTENTICACIÓN POR API KEY ---
async def require_api_key(request: Request):
    """Dependencia que exige siempre X-API-Key en el header o query param para endpoints sensibles."""
    key = request.headers.get("X-API-Key", "")
    if not key:
        key = request.query_params.get("api_key", "")
        
    if key != ZODIT_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid API Key.")
    return True

# --- TELEMETRÍA ---
system_logs = []

def add_log(event, details):
    global system_logs
    entry = {"timestamp": datetime.now().strftime("%H:%M:%S"), "event": event, "details": str(details)}
    system_logs.append(entry)
    system_logs = system_logs[-100:]
    print(f"[{entry['timestamp']}] {event}: {details}")

def truncate(s, length):
    """Safe truncation for type checkers."""
    st = str(s)
    if len(st) <= length:
        return st
    return str(cast(Any, st)[:length])

# --- CONFIGURACIÓN DINÁMICA ---
def get_best_available_model(preferred_model: str) -> str:
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read())
            models = [m["name"] for m in data.get("models", [])]
            if not models: return preferred_model
            if preferred_model in models: return preferred_model
            for m in models:
                if "llama" in preferred_model.lower() and "llama" in m.lower(): return m
                if "qwen" in preferred_model.lower() and "qwen" in m.lower(): return m
                if "gemma" in preferred_model.lower() and "gemma" in m.lower(): return m
                if "phi" in preferred_model.lower() and "phi" in m.lower(): return m
                if "deepseek" in preferred_model.lower() and "deepseek" in m.lower(): return m
            return models[0]
    except Exception as e:
        print(f"Warning: Could not fetch Ollama models: {e}")
        return preferred_model

def load_settings():
    default = {
        "agent_name": "JARVIS",
        "personality_prompt": (
            "Eres JARVIS, un Asistente Humano de élite, inteligente, proactivo y sumamente refinado. "
            "Tu tono es el de un mayordomo digital sofisticado: profesional, servicial, cálido y brillante. "
            "Te diriges al usuario como 'Señor' o 'Danie' con un respeto genuino y una eficiencia técnica impecable.\n\n"
            "### PROTOCOLO DE CONTROL DE COMANDOS\n"
            "1. **Interpretación Activa**: Analiza cada solicitud para determinar si requiere una acción (herramienta) o una respuesta informativa.\n"
            "2. **Uso de Herramientas**: Si una herramienta puede proporcionar el dato exacto o realizar la acción solicitada, ÚSALA de inmediato. No preguntes si debes hacerlo si la intención es clara.\n"
            "3. **Transparencia Elegante**: Realiza las llamadas a herramientas de forma silenciosa. Una vez obtenida la información, preséntala de manera natural y coherente.\n"
            "4. **Manejo de Ambigüedad**: Si una solicitud es vaga (ej. 'abre eso'), intenta deducir el contexto del historial. Si persiste la duda, pide clarificación brevemente.\n\n"
            "### REGLAS DE COMUNICACIÓN CRÍTICAS\n"
            "- **NUNCA** menciones nombres de funciones (ej. `web_search`), formatos JSON o detalles técnicos de la implementación en tu respuesta final.\n"
            "- **ESTILO**: Usa un lenguaje humano fluido. Evita listas robóticas si no son necesarias. Prefiere el diálogo elegante.\n"
            "- **ANTICIPACIÓN**: Si el usuario pide algo que requiere varios pasos, ejecuta la secuencia lógica o informa que estás en ello.\n"
            "- **RESPONDE SIEMPRE EN ESPAÑOL**, con la elegancia que caracteriza a un asistente de clase mundial."
        ),
        "model_name": "qwen3.5:4b",
        "vision_model": "llava-phi3:latest",
        "transcription_model": "small",
        "require_confirmation": True,
        "history_limit": 6,
        "temperature": 0.7,
        "top_p": 0.8,
        "whisper_prompt": "Zodit, Mandev, WhatsApp, Chrome, YouTube, abre, cierra, procesos, captura.",
        "enabled_tools": ["pc", "whatsapp", "rag", "vision", "voice", "calendar"]
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return {**default, **json.load(f)}
        except: return default
    return default

settings = load_settings()
MODEL = get_best_available_model(settings.get("model_name", "qwen3.5:4b"))
VISION_MODEL = get_best_available_model(settings.get("vision_model", "llava-phi3:latest"))

# Persistir modelos detectados para mantener herramientas en sincronía
if MODEL != settings.get("model_name") or VISION_MODEL != settings.get("vision_model"):
    settings["model_name"] = MODEL
    settings["vision_model"] = VISION_MODEL
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except: pass

# El dispatcher ahora usa el mismo modelo que el chat general (MODEL)
INTEGRATIONS_FILE = os.path.join(ASSETS_DIR, "integrations.json")


# --- SKILLS LOADER ---
SKILLS_ROOT = os.path.join(BASE_DIR, "skills")

def load_custom_skills():
    """Busca en /skills/*/SKILL.md e instrucciones para inyectar al prompt."""
    skill_prompts = []
    if not os.path.exists(SKILLS_ROOT): return ""
    
    for folder in os.listdir(SKILLS_ROOT):
        folder_path = os.path.join(SKILLS_ROOT, folder)
        if os.path.isdir(folder_path):
            skill_md = os.path.join(folder_path, "SKILL.md")
            if os.path.exists(skill_md):
                try:
                    with open(skill_md, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Extraer solo el contenido después del frontmatter si existe
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3: content = parts[2].strip()
                        skill_prompts.append(f"### SKILL: {folder.upper()}\n{content}")
                except: pass
    
    if skill_prompts:
        return "\n\n--- INSTRUCCIONES DE HABILIDADES ADICIONALES ---\n" + "\n\n".join(skill_prompts)
    return ""

# --- MEMORIA ---
def load_memories():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except: return {}
    return {}

user_memories = load_memories()

@app.api_route("/api/settings", methods=["GET", "POST", "OPTIONS"])
async def api_settings(request: Request):
    global settings, MODEL
    if request.method == 'OPTIONS': 
        return JSONResponse(content="")
        
    if request.method == 'POST':
        new_data = await request.json()
        settings.update(new_data)
        if not os.path.exists(ASSETS_DIR): os.makedirs(ASSETS_DIR, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        MODEL = get_best_available_model(settings.get("model_name", "llama3.1:8b"))
        global VISION_MODEL
        VISION_MODEL = get_best_available_model(settings.get("vision_model", "llama3.2-vision:latest"))
        return JSONResponse(content={"status": "success", "settings": settings})
        
    return JSONResponse(content=settings)

def load_integrations():
    path = os.path.join(ASSETS_DIR, "integrations.json")
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading integrations:", e)
        return []

def save_integrations(data):
    path = os.path.join(ASSETS_DIR, "integrations.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# =================================================================
# CONTEXTO DE SESIÓN (delegado a session_manager)
# =================================================================

def get_session(sender: str) -> dict:
    """Wrapper sobre session_manager.get_session para mantener API actual."""
    return _base_get_session(sender)


def save_session(sender: str, **kwargs):
    """Persistencia de sesión con límite de historial basado en settings."""
    history_limit = settings.get("history_limit", 6)
    _base_save_session(sender, history_limit=history_limit, **kwargs)


def prune_sessions():
    """Recorta sesiones huérfanas o antiguas en memoria."""
    _base_prune_sessions()

# =================================================================
# NLU & REGEX
# =================================================================
CONFIRM_RE = re.compile(r'\b(?:si|dale|confirma|envialo|ok|procede)\b', re.I)
CANCEL_RE  = re.compile(r'\b(?:no|cancela|espera|deten)\b', re.I)

def is_tool_enabled(name: str):
    """Verifica si una herramienta está habilitada en integrations.json."""
    integrations = load_integrations()
    for item in integrations:
        if item.get("id") == name:
            return item.get("enabled", True)
    return True # Default enabled if not found

def run_component(category, name, *args):
    arg_str = " | ".join([truncate(str(a), 20) for a in args])
    add_log(f"RUN_{category.upper()}", f"Tool: {name} | Args: {arg_str}")
    
    if not is_tool_enabled(name if category == "tool" else category):
        add_log("RUN_BLOCKED", f"Tool {name} is disabled.")
        return f"Error: La herramienta '{name}' está desactivada."
        
    paths = {
        "tool": {
            "rag": os.path.join(SCRIPTS_DIR, "rag_tool.py"), 
            "voice": os.path.join(SCRIPTS_DIR, "transcribe_tool.py"), 
            "pc": os.path.join(SCRIPTS_DIR, "pc_executor.py"), 
            "vision": os.path.join(SCRIPTS_DIR, "vision_tool.py"),
            "calendar": os.path.join(SCRIPTS_DIR, "calendar_tool.py"),
            "tts": os.path.join(SCRIPTS_DIR, "tts_tool.py"),
            "search": os.path.join(SCRIPTS_DIR, "search_tool.py"),
            "system": os.path.join(SCRIPTS_DIR, "system_tool.py")
        },
        "agent": {"sales": os.path.join(SCRIPTS_DIR, "sales_agent.py")}
    }
    
    path = paths.get(category, {}).get(name)
    if not path or not os.path.exists(path): 
        add_log("RUN_ERROR", f"Path not found for {name}")
        return "Error: No hallado."
        
    try:
        # Llamada SEGURA: sin shell=True, argumentos como lista (evita inyección de comandos)
        cmd_list = PYTHON_ARGS + [path] + [str(a) for a in args]
        res = subprocess.check_output(cmd_list, shell=False, timeout=300).decode('utf-8', errors='ignore').strip()
        add_log("RUN_OK", f"{name} finished.")
        return res
    except Exception as e:
        add_log("RUN_FAIL", f"{name} error: {str(e)}")
        return f"Error: {str(e)}"

def get_live_screenshot():
    try:
        req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/vision/screenshot")
        if ZODIT_API_KEY: req.add_header('X-API-Key', ZODIT_API_KEY)
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read())
            if data.get("status") == "success":
                path = os.path.join(ASSETS_DIR, "live_screen.jpg")
                with open(path, "wb") as f: f.write(base64.b64decode(data["image_base64"].split(",")[1]))
                return run_component("tool", "vision", path)
    except: return "Error capturando pantalla."

def send_to_whatsapp(msg: str, phone: str):
    """Envía un mensaje usando el microservicio node-whatsapp."""
    try:
        # Si el número viene como admin_hub o similar, no procesar como phone real
        if not phone or len(str(phone)) < 5:
            add_log("WHATSAPP_SIM", f"Ignoring non-phone target: {phone}")
            return "Error: Número de teléfono inválido."
            
        data = json.dumps({"phone": phone, "message": msg}).encode('utf-8')
        req = urllib.request.Request(f"{WHATSAPP_BASE_URL}/send", data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        if ZODIT_API_KEY: req.add_header('X-API-Key', ZODIT_API_KEY)
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.read().decode('utf-8')
    except Exception as e:
        add_log("WHATSAPP_ERR", str(e))
        return f"Error envíando WhatsApp: {e}"

def route_request(text: str, hint: str = "", has_image: bool = False, custom_model: str | None = None) -> list:
    add_log("IA_ROUTER_START", f"Routing: {truncate(text, 30)} (Img: {has_image})")
    
    examples = (
        "Ejemplos de ruteo:\n"
        "1. 'Agéndame reunión con Juan mañana a las 3' -> [{\"tool\": \"CALENDAR\", \"params\": \"Reunión Juan\", \"body\": \"2026-03-02T15:00:00\", \"msg\": \"Agendando reunión...\"}]\n"
        "2. 'Abre opera y dile a Carlos que voy' -> [{\"tool\": \"PC\", \"params\": \"opera\"}, {\"tool\": \"WHATSAPP\", \"params\": \"Carlos\", \"body\": \"Ya voy\"}]\n"
        "3. '¿Qué ves en pantalla?' -> [{\"tool\": \"PC\", \"params\": \"screenshot\", \"msg\": \"Mirando la pantalla...\"}]\n"
        "4. 'Investiga la red sobre los nuevos chips M4' -> [{\"tool\": \"SEARCH\", \"params\": \"chips Apple M4\", \"msg\": \"Investigando en la red...\"}]\n"
        "5. 'Dame un consejo sobre fitness' -> [{\"tool\": \"CHAT\", \"msg\": \"Buscando consejos proactivos...\"}]\n"
        "6. 'Hola, ¿qué tal hoy?' -> [{\"tool\": \"CHAT\", \"msg\": \"Curioseando el día...\"}]\n"
    )

    now_dt = datetime.now()
    now_str = now_dt.strftime("%Y-%m-%dT%H:%M:%S")
    day_name = now_dt.strftime("%A") # Ej: Monday
    
    # Build dynamic tool list from integrations.json
    integrations = load_integrations()
    enabled_tools = {i['id'] for i in integrations if i.get('enabled', True)}
    
    tool_descriptions = []
    if 'pc' in enabled_tools:
        tool_descriptions.append("- PC (params: 'screenshot'|'calc'|'open:APP_NAME')")
    if 'whatsapp' in enabled_tools:
        tool_descriptions.append("- WHATSAPP (params: nombre_contacto, body: mensaje)")
    if 'calendar' in enabled_tools:
        tool_descriptions.append("- CALENDAR (params: titulo, body: ISO-8601). Solo si hay fecha/hora explícita.")
    if 'search' in enabled_tools:
        tool_descriptions.append("- SEARCH (params: query_busqueda)")
    if 'rag' in enabled_tools:
        tool_descriptions.append("- RAG (params: consulta). Para buscar en conocimiento local.")
    tool_descriptions.append("- ASK (msg: pregunta al usuario)")
    tool_descriptions.append("- THINK (msg: razonamiento interno)")
    tool_descriptions.append("- CHAT (msg: respuesta). Default para charla o dudas.")
    tools_str = "\n".join(tool_descriptions)

    prompt = (
        f"SISTEMA: Eres el despachador de herramientas de Zodit Omni. Hoy: {day_name}, {now_str}.\n"
        f"INPUT DEL USUARIO: '{text}'\n"
        f"CONTEXTO: {hint}\nIMÁGEN: {has_image}\n\n"
        f"HERRAMIENTAS DISPONIBLES (solo estas):\n{tools_str}\n\n"
        "REGLAS ESTRICTAS:\n"
        "1. Responde ÚNICAMENTE con un array JSON. Sin texto extra. Sin markdown.\n"
        "2. Si hay imagen, usa CHAT (el análisis visual se hará por separado).\n"
        "3. Si el mensaje es charla casual, saludo o pregunta general -> CHAT.\n"
        "4. CALENDAR solo si hay fecha o hora EXPLÍCITA en el mensaje.\n"
        "5. Puedes encadenar múltiples tools en el array.\n"
        f"{examples}\n"
        "RESPUESTA JSON:"
    )
    
    # Dispatcher usa el modelo general (MODEL).
    # Si hay imagen, el análisis profundo se hace en el CHAT handler con VISION_MODEL.
    dispatch_model = custom_model or MODEL
    data = {"model": dispatch_model, "prompt": prompt, "stream": False, "format": "json"}
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps(data).encode('utf-8'))
        with urllib.request.urlopen(req, timeout=30) as res:
            response_data = json.loads(res.read())['response']
            
            # Robustez para DeepSeek-R1: quitar tags <think> si el modelo los incluyó
            if "<think>" in response_data:
                response_data = re.sub(r'<think>.*?</think>', '', response_data, flags=re.DOTALL).strip()
            
            try:
                actions = json.loads(response_data)
                if isinstance(actions, dict): actions = [actions]
                add_log("IA_ROUTER_OK", f"Actions: {len(actions)}")
                return actions
            except json.JSONDecodeError:
                add_log("IA_ROUTER_PARSE_ERR", f"Failed parsing: {response_data}")
                return [{"tool": "CHAT", "msg": "Entendido. Procesando tu solicitud."}]
    except Exception as e: 
        add_log("IA_ROUTER_FAIL", str(e))
        return [{"tool": "CHAT", "msg": "Procesando de forma estándar."}]

# =================================================================
# ORQUESTADOR PRINCIPAL
# =================================================================
async def orchestrate(message: str, sender: str, is_owner: bool, audio_path: str | None = None, image_path: str | None = None, return_response: bool = False, custom_model: str | None = None):
    """
    Orquesta el flujo completo de un mensaje de usuario.

    Si `return_response` es True, devuelve una tupla (response: str, tools_used: list[str]).
    En modo webhook/WhatsApp, ejecuta side-effects y retorna None.
    """
    try:
        if not is_owner:
            return
        prune_sessions()
        add_log("ORCHESTRATE_START", f"Msg de {sender}")
        text = str(message)
        ctx = get_session(sender)

        if audio_path: 
            add_log("ORCHESTRATE_VOICE", "Processing audio...")
            text = run_component("tool", "voice", audio_path)
            add_log("ORCHESTRATE_VOICE_OK", f"Transcribed: {truncate(text, 30)}")
            
        if image_path:
            add_log("ORCHESTRATE_VISION", "Processing image...")
            v = run_component("tool", "vision", image_path)
            text = f"{text}\n[Vision: {v}]"
            add_log("ORCHESTRATE_VISION_OK", "Vision processed.")

        if not text: 
            add_log("ORCHESTRATE_EMPTY", "Empty message after processing.")
            return

        # =================================================================
        # 0. SEMANTIC CACHE CHECK (SPEED & COST REDUCTION)
        # =================================================================
        cached_response = await semantic_cache.check_cache(text)
        if cached_response:
            badge = "⚡ *[Cache HIT]*\n\n"
            final_resp = badge + cached_response
            add_log("CACHE_HIT", "Recovered from Semantic Vector DB.")
            metrics.record_cache_hit()
            metrics.record_request(sender=sender, tool="CACHE")
            if return_response:
                return final_resp, ["CACHE"]
            send_to_whatsapp(final_resp, sender)
            return
        else:
            metrics.record_cache_miss()

        # 1. Ejecutar detecciones rápidas (Regex) para PC y Mensajería directa
        pc_cmds = detect_pc_commands(text)
        if pc_cmds:
            results = []
            tools_used = ["PC"]
            for c in pc_cmds:
                if c == "help":
                    try:
                        with open(os.path.join(BASE_DIR, "JARVIS_COMMANDS.md"), "r", encoding="utf-8") as f:
                            help_text = f.read()
                        results.append(help_text)
                    except: results.append("No pude leer la guía de comandos.")
                else:
                    res = run_component('tool', 'pc', c)
                    if isinstance(res, str) and res.startswith("SCREENSHOT_SAVED:"):
                        shot_path = res.split(":", 1)[1].strip()
                        add_log("VISION_START", f"Fast Route Analyzing: {shot_path}")
                        tools_used.append("VISION")
                        try:
                            vision_res = run_component("tool", "vision", shot_path)
                            res = f"Visión:\n{vision_res}"
                        except Exception as ve:
                            res = f"Captura tomada pero falló análisis: {ve}"
                    results.append(res)
            
            # Si detectamos un comando claro, reseteamos el intent para que no sea pegajoso
            save_session(sender, last_intent="CHAT")
            
            if return_response: return "\n\n".join(results), tools_used
            send_to_whatsapp("\n\n".join(results), sender)
            return

        send_list = parse_send_commands(text, sender)
        if send_list:
            for s in send_list:
                contact, body = s['contact'], s['body']
                # Resolver número desde la base de conocimiento local sin subprocess
                rag_result = rag_tool.query_knowledge(contact)
                phone = extract_phone_number(rag_result)
                if phone:
                    send_to_whatsapp(body, phone)
                    send_to_whatsapp(f"[OK] Mensaje enviado a {contact}", sender)
            save_session(sender, last_intent="CHAT")
            return

        # 2. Cerebro LLM para multi-comandos e intents complejos
        add_log("ORCHESTRATE_LLM", "Analyzing actions...")
        
        # --- RECUERDOS A LARGO PLAZO ---
        memories = rag_tool.query_memories(text)
        memory_hint = f"\nRecuerdos pasados relevantes:\n{memories}" if memories else ""
        
        # Construir contexto de conversación
        history_str = ""
        for h in ctx.get("history", []):
            role = "Usuario" if h["role"] == "user" else "Zodit"
            history_str += f"{role}: {h['content']}\n"
        
        # Si el mensaje es corto o negación, bajamos prioridad al intent previo
        is_pivot = any(word in text.lower() for word in ["no", "cancela", "olvida", "nada", "anormal"])
        intent_hint = f"Intent Previo: {ctx['last_intent']}" if ctx.get('last_intent') and not is_pivot else "Sin intent previo."
        
        actions = route_request(text, f"Historial:\n{history_str}\n{memory_hint}\n{intent_hint}", has_image=(image_path is not None))
        
        # Validar si hay herramientas que darán respuesta o acción válida al usuario
        has_response_tool = any(a.get("tool", "").upper() in ["CHAT", "ASK", "CALENDAR", "WHATSAPP", "PC", "SEARCH"] for a in actions)
        if not has_response_tool and len(actions) > 0:
            actions.append({"tool": "CHAT", "msg": "Fallback chat para responder al usuario"})
        
        final_confirmations = []
        tools_used = []
        for act in actions:
            tool = act.get("tool", "CHAT")
            params = act.get("params", "")
            body = act.get("body", "")
            msg = act.get("msg", "")

            add_log("ACTION_EXEC", f"Tool: {tool}")
            tools_used.append(tool)
            
            if tool == "PC":
                pc_result = run_component("tool", "pc", params or body or "screenshot" if params == "screenshot" else params or body)
                
                if isinstance(pc_result, str) and pc_result.startswith("SCREENSHOT_SAVED:"):
                    # Native screenshot was taken — pipe to vision model for analysis
                    shot_path = pc_result.split(":", 1)[1].strip()
                    add_log("VISION_START", f"Analyzing screenshot: {shot_path}")
                    tools_used.append("VISION")
                    try:
                        vision_result = run_component("tool", "vision", shot_path)
                        final_confirmations.append(f"Descripcion de pantalla:\n{vision_result}")
                    except Exception as ve:
                        final_confirmations.append(f"Captura tomada pero no pude analizar la imagen: {ve}")
                elif params == "screenshot":
                    # Fallback path (old behavior)
                    res = get_live_screenshot()
                    final_confirmations.append(f"Pantalla: {res}")
                else:
                    if pc_result: final_confirmations.append(pc_result)
                    elif msg: final_confirmations.append(msg)

            
            elif tool == "WHATSAPP":
                target_name = params or body
                # Resolver número desde RAG en proceso
                rag_result = rag_tool.query_knowledge(target_name)
                phone = extract_phone_number(rag_result)
                if phone:
                    send_to_whatsapp(body or text, phone)
                    final_confirmations.append(f"Mensaje enviado a {target_name}.")
                else:
                    final_confirmations.append(f"No hallé el número de {target_name}.")

            elif tool == "CALENDAR":
                # Fallback: Si no hay params ni body, es un error del LLM. Cambiamos a CHAT.
                if not params and not body:
                    add_log("RUN_FAIL", "Calendar with no data. Pivoting to CHAT.")
                    # Continuar a la siguiente acción o insertar un CHAT
                    actions.append({"tool": "CHAT", "msg": "Entendido. ¿Para cuándo quieres agendar este evento?"})
                    continue
                # Calendar espera: summary, start_time, duration
                res = run_component("tool", "calendar", params, body, "60")
                final_confirmations.append(res)
                
            elif tool == "ASK":
                question = params or body or msg
                final_confirmations.append(question)
                break # Rompe la cadena de ejecución si necesita confirmación
                
            elif tool == "SEARCH":
                query = params or body or text
                res = run_component("tool", "search", query)
                add_log("RUN_OK", f"Search finished for: {truncate(query, 20)}")
                final_confirmations.append(f"Resultados de búsqueda: {res}")

            elif tool == "THINK":
                thought = params or body or msg
                add_log("IA_THOUGHT", thought)
                # Mantener el pensamiento en el historial
                save_session(sender, history_append={"role": "assistant", "content": f"*Pensando: {thought}*"})
                continue

            elif tool == "CHAT":
                integrations = load_integrations()
                rag_enabled = any(i['id'] == 'rag' and i.get('enabled') for i in integrations)
                
                rag_context = ""
                if rag_enabled:
                    try:
                        rag_context = rag_tool.query_knowledge(text)
                    except Exception as e:
                        add_log("RAG_CHAT_FAIL", str(e))
                        rag_context = ""
                
                rag_section = f"\n\nCONTEXTO DE BASE DE DATOS LOCAL:\n{rag_context}" if rag_context else "\n\nCONTEXTO DE BASE DE DATOS LOCAL: [Sin datos relevantes encontrados]"

                # Inyección de Guía de Comandos
                help_keywords = ["ayuda", "comandos", "instrucciones", "que puedes hacer"]
                guide_hint = ""
                if any(k in text.lower() for k in help_keywords):
                    try:
                        with open(os.path.join(BASE_DIR, "JARVIS_COMMANDS.md"), "r", encoding="utf-8") as f:
                            guide_hint = f"\nGUÍA DE COMANDOS:\n{f.read()}"
                    except: pass

                system_prompt = settings.get('personality_prompt', 'Eres Zodit.')
                # Inyectar Skills Dinámicas
                custom_skills = load_custom_skills()
                system_prompt += custom_skills
                # BLOQUE ANTI-ALUCINACIÓN
                anti_hallucination = (
                    "\n\nREGLAS ANTI-ALUCINACIÓN (OBLIGATORIAS):\n"
                    "1. Si el Contexto de la Base de Datos dice 'Sin datos relevantes' o está vacío, "
                    "responde honestamente que no tienes esa información. NUNCA inventes datos, nombres, cifras o fechas.\n"
                    "2. Si el contexto sí contiene datos, úsalos directamente y sé preciso.\n"
                    "3. Distingue claramente entre lo que sabes (contexto RAG) y lo que estás razonando."
                )
                sys_msg = f"{system_prompt}{anti_hallucination}{rag_section}{guide_hint}"
                
                # Limitar historial
                raw_limit = settings.get("history_limit", 6)
                try: h_limit = int(float(str(raw_limit)))
                except: h_limit = 6
                hist = ctx.get("history", [])
                if len(hist) > h_limit:
                    hist = hist[-h_limit:]
                
                # Transformar historial para la API de Ollama
                messages = [{"role": "system", "content": sys_msg}]
                for h in hist:
                    messages.append({"role": h["role"], "content": h["content"]})
                messages.append({"role": "user", "content": text})
                
                # Seleccionar modelo (Visión vs Texto)
                if image_path:
                    chat_model = VISION_MODEL
                elif custom_model:
                    chat_model = custom_model
                else:
                    chat_model = MODEL
                
                data = {
                    "model": chat_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": float(settings.get("temperature", 0.7)),
                        "top_p": float(settings.get("top_p", 0.8))
                    }
                }
                
                # Si hay imagen en un request de chat, añadirla codificada
                if image_path:
                    try:
                        with open(image_path, "rb") as img_file:
                            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                        messages[-1]["images"] = [encoded_string]
                    except Exception as e:
                        add_log("CHAT_IMAGE_ERR", str(e))

                add_log("IA_CHAT_START", f"Modelo: {chat_model} | RAG: {len(rag_context)}")
                try:
                    async with httpx.AsyncClient(timeout=120) as client:
                        resp_data = await client.post("http://127.0.0.1:11434/api/chat", json=data)
                        if resp_data.status_code == 200:
                            reply = resp_data.json()['message']['content'].strip()
                            add_log("IA_CHAT_OK", f"Respuesta generada ({len(reply)} chars)")
                            final_confirmations.append(reply)
                        else:
                            raise Exception(f"HTTP {resp_data.status_code}")
                except Exception as e:
                    add_log("IA_CHAT_FAIL", str(e))
                    final_confirmations.append("Tuve un problema conectando con mi núcleo cognitivo. Intenta de nuevo.")
            
            # Si la herramienta fue ASK, mantenemos el intent para la siguiente vuelta, 
            # de lo contrario, si fue CHAT o terminó, limpiamos para no ser pegajosos.
            new_intent = tool if tool == "ASK" else "CHAT"
            save_session(sender, last_intent=new_intent)

        if final_confirmations:
            resp = "\n\n".join(final_confirmations)
            
            # SEMANTIC CACHE STORE (ONLY FOR LLM/SEARCH INTENTS)
            if "CHAT" in tools_used or "SEARCH" in tools_used:
                await semantic_cache.store_in_cache(text, resp)
            
            # Voice reply
            voice_path = None
            try:
                fresh_settings = load_json_settings()
                if fresh_settings.voice_reply_enabled and (audio_path or "quieres hablar" in text.lower()):
                    add_log("TTS_START", "Generando respuesta de voz...")
                    voice_file = os.path.join(BASE_DIR, "assets", f"resp_{int(datetime.now().timestamp())}.mp3")
                    run_component("tool", "tts", resp, voice_file)
                    if os.path.exists(voice_file):
                        voice_path = voice_file
            except Exception as e:
                add_log("TTS_FAIL", f"TTS validation error: {e}")
            
            if not return_response:
                send_to_whatsapp(resp, sender, media_path=voice_path)
            
            # Guardar en memoria
            save_session(sender, history_append={"role": "user", "content": text})
            save_session(sender, history_append={"role": "assistant", "content": resp})
            
            # --- AUTO-RESUMEN Y PERSISTENCIA DE MEMORIA ---
            hist = ctx.get("history", [])
            if len(hist) >= 10: # Cada 5 intercambios (User + Assistant)
                add_log("MEMORY_SAVE", "Generando resumen para memoria...")
                
                # Usar Ollama directamente para resumir (evitar route_request que es para herramientas)
                summary_prompt = f"Resume brevemente estos puntos clave de la conversación para recordarlos luego (máximo 2 líneas):\n{history_str}"
                try:
                    data = {
                        "model": MODEL, 
                        "messages": [{"role": "user", "content": summary_prompt}], 
                        "stream": False
                    }
                    async with httpx.AsyncClient(timeout=30) as client:
                        resp_data = await client.post("http://127.0.0.1:11434/api/chat", json=data)
                        if resp_data.status_code == 200:
                            ans = resp_data.json()['message']['content']
                            if ans:
                                rag_tool.add_memory(ans, {"sender": sender, "date": datetime.now().isoformat()})
                                add_log("MEMORY_SAVE_OK", "Resumen guardado.")
                except Exception as e:
                    add_log("MEMORY_SAVE_FAIL", str(e))
                
                # Limpiar historial para liberar contexto pero mantener base reciente
                ctx["history"] = ctx["history"][-4:] 
            
            add_log("ORCHESTRATE_END", "OK")
            if return_response: return resp, tools_used
        else:
            add_log("ORCHESTRATE_END", "No response generated.")
            if return_response: return "Done.", []

    except Exception as e:
        import traceback
        add_log("ORCHESTRATE_FATAL", str(e))
        print(traceback.format_exc())
        if return_response: return f"Error: {str(e)}", []

async def dispatch_async(message: str, sender: str, is_owner: bool, audio_path: str | None = None, image_path: str | None = None) -> None:
    """Ejecuta orquestación asíncrona dentro de la misma request sin bloquear el I/O loop principal (coroutine fallback)"""
    try:
        await orchestrate(message, sender, is_owner, audio_path, image_path)
    except Exception as e:
        log.error(f"Error in async dispatch: {e}")

class WebhookPayload(BaseModel):
    message: str = ""
    sender: str = ""
    isOwner: bool = False
    audioPath: str | None = None
    imagePath: str | None = None

@app.post("/webhook")
async def webhook(payload: WebhookPayload):
    # Se recomienda usar BackgroundTasks para webhooks en el futuro, por ahora await simple fire & forget (o dispatch asíncrono)
    asyncio.create_task(
        dispatch_async(
            payload.message,
            payload.sender,
            payload.isOwner,
            payload.audioPath,
            payload.imagePath,
        )
    )
    return {"status": "ok"}

@app.get("/status")
async def api_status(): 
    """Legacy status endpoint."""
    return {"status": "online", "service": "gateway"}

@app.get("/health")
async def api_health():
    """
    Comprehensive health check.
    Checks connectivity to Tool Server and WhatsApp microservices.
    """
    health_report = {
        "status": "online",
        "service": "gateway",
        "timestamp": datetime.now().isoformat(),
        "dependencies": {
            "tool_server": "offline",
            "whatsapp": "offline"
        }
    }
    
    # Check Tool Server
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT_TOOLS}/api/system/health", headers={'X-API-Key': ZODIT_API_KEY})
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.getcode() == 200:
                health_report["dependencies"]["tool_server"] = "online"
    except:
        pass

    # Check WhatsApp Server
    try:
        # Assuming WhatsApp server has a status or health endpoint at root or /status
        req = urllib.request.Request(f"http://127.0.0.1:{PORT_WHATSAPP}/status")
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.getcode() == 200:
                health_report["dependencies"]["whatsapp"] = "online"
    except:
        pass

    return jsonify(health_report)

@app.route('/api/telemetry')
@require_api_key
def get_telemetry():
    return jsonify({"logs": system_logs[-100:]})

@app.route('/api/models', methods=['GET'])
def list_ollama_models():
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as res:
            return res.read().decode('utf-8'), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"models": [], "error": str(e)}), 500

@app.route('/api/rag/files', methods=['GET'])
@require_api_key
def list_rag_files():
    # Ruta dinámica, configurable desde .env (RAG_DRIVE_PATH)
    path = RAG_DRIVE_PATH
    if not os.path.exists(path):
        return jsonify({"files": [], "error": f"Ruta '{path}' no encontrada. Verifica RAG_DRIVE_PATH en .env"})

    files = []
    for f in os.listdir(path):
        if f.endswith(('.xlsx', '.csv', '.txt', '.pdf')):
            full = os.path.join(path, f)
            stats = os.stat(full)
            files.append({
                "name": f,
                "size": stats.st_size,
                "last_mod": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    return jsonify({"files": files})

class TestChatRequest(BaseModel):
    message: str = ""

@app.post("/api/test_chat")
async def api_test_chat(data: TestChatRequest):
    asyncio.create_task(orchestrate(data.message, "admin_hub", True))
    return {"status": "sent", "response": "Procesado (revisa el Monitor)"}

class ApiChatRequest(BaseModel):
    message: str = ""
    model: str | None = None

@app.post("/api/chat")
async def api_chat(data: ApiChatRequest):
    """Endpoint sincronico para la UI estilo Zodit Omni. Devuelve tools_used para badges."""
    msg = data.message
    model = data.model
    
    if not msg:
        return {"response": "Mensaje vacio.", "tools_used": []}
        
    try:
        result = await orchestrate(msg, sender="admin_webui", is_owner=True, return_response=True, custom_model=model)
        if isinstance(result, tuple):
            resp, tools_used = result
        else:
            resp, tools_used = result, []
        return {"response": resp or "Procesado.", "tools_used": tools_used}
    except Exception as e:
        return JSONResponse(status_code=500, content={"response": f"Error interno: {str(e)}", "tools_used": []})

@app.get("/api/tools/list")
async def list_tools(_=Depends(require_api_key)):
    files = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.py') or f.endswith('.js')]
    return {"tools": files}

class ToolCodeRequest(BaseModel):
    file: str
    code: str | None = None

@app.api_route("/api/tools/code", methods=["GET", "POST"])
async def tool_code(request: Request, _=Depends(require_api_key)):
    if request.method == "GET":
        filename = request.query_params.get("file", "")
    else:
        req_json = await request.json()
        filename = req_json.get("file", "")
        
    if not filename: return JSONResponse(status_code=400, content={"error": "No file"})
    # Sanitizar: evitar path traversal
    filename = os.path.basename(filename)
    path = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.exists(path): return JSONResponse(status_code=403, content={"error": "Invalid file"})

    if request.method == "GET":
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return {"code": f.read()}
    else:
        code = req_json.get("code")
        if code is None: return JSONResponse(status_code=400, content={"error": "No code provided"})
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
        return {"status": "saved"}

@app.get("/api/integrations")
async def get_integrations():
    return load_integrations()

class ToggleIntegrationRequest(BaseModel):
    id: str
    enabled: bool

@app.post("/api/integrations/toggle")
async def toggle_integration(data: ToggleIntegrationRequest):
    tool_id = data.id
    enabled = data.enabled
    
    integrations = load_integrations()
    for item in integrations:
        if item['id'] == tool_id:
            item['enabled'] = bool(enabled)
            break
            
    save_integrations(integrations)
    add_log('INTEGRATION_TOGGLE', f'{tool_id} -> {enabled}')
    return {'status': 'ok', 'id': tool_id, 'enabled': enabled}

if __name__ == "__main__":
    import uvicorn
    key_status = "CONFIGURADA [OK]" if ZODIT_API_KEY and ZODIT_API_KEY != "CHANGE_ME_TO_A_RANDOM_SECRET_KEY" else "[!] NO CONFIGURADA -- edita .env"
    log.info(f"[AUTH] API Key: {key_status}")
    log.info(f"[NET] Gateway corriendo en: http://0.0.0.0:{PORT_GATEWAY}")
    uvicorn.run("main_agent:app", host="0.0.0.0", port=PORT_GATEWAY, reload=True)