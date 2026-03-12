import os
import subprocess
import base64
import urllib.parse
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

# --- Puertos desde .env ---
PORT_TOOLS = int(os.getenv("PORT_TOOLS", 5005))
ZODIT_API_KEY = os.getenv("ZODIT_API_KEY", "")

if not ZODIT_API_KEY or ZODIT_API_KEY == "CHANGE_ME_TO_A_RANDOM_SECRET_KEY":
    raise RuntimeError(
        "ZODIT_API_KEY no está configurada o usa un valor débil. "
        "Configura una clave segura en el archivo .env antes de iniciar el Tool Server."
    )

# =================================================================
# AUTENTICACIÓN POR API KEY (Soporta TailScale y LAN remota)
# =================================================================
def require_api_key(f):
    """Middleware que exige siempre X-API-Key en el header para endpoints sensibles."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if key != ZODIT_API_KEY:
            return jsonify({"status": "error", "message": "Unauthorized. Invalid API Key."}), 401
        return f(*args, **kwargs)
    return decorated

# =================================================================
# PYAUTOGUI - importar con FAILSAFE HABILITADO
# =================================================================
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
    # FAILSAFE = True es la configuración SEGURA. Si el mouse llega a la esquina
    # superior izquierda, PyAutoGUI lanzará FailSafeException y detendrá el control.
    pyautogui.FAILSAFE = True
    print("[OK] PyAutoGUI cargado con FAILSAFE=True (seguro)")
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[WARN] PyAutoGUI no instalado. Mouse, teclado y visión deshabilitados.")
    print("-> pip install pyautogui")

# =================================================================
# ALLOWLIST ESTRICTA DE APLICACIONES (Anti-Inyección de Comandos)
# =================================================================
APP_ALLOWLIST = {
    "calculadora": ["calc.exe"],
    "calc":        ["calc.exe"],
    "notepad":     ["notepad.exe"],
    "explorador":  ["explorer.exe"],
    "word":        ["cmd.exe", "/c", "start", "winword"],
    "excel":       ["cmd.exe", "/c", "start", "excel"],
    "edge":        ["cmd.exe", "/c", "start", "msedge"],
    "chrome":      ["cmd.exe", "/c", "start", "chrome"],
    "opera":       ["cmd.exe", "/c", "start", "opera"],
    "brave":       ["cmd.exe", "/c", "start", "brave"],
    "cmd":         ["cmd.exe"],
    "terminal":    ["cmd.exe"],
    "navegador":   ["cmd.exe", "/c", "start", "msedge"],
    "powerpoint":  ["cmd.exe", "/c", "start", "powerpnt"],
    "vscode":      ["cmd.exe", "/c", "start", "code"],
    "spotify":     ["cmd.exe", "/c", "start", "spotify"],
    "discord":     ["cmd.exe", "/c", "start", "discord"],
    "whatsapp":    ["cmd.exe", "/c", "start", "whatsapp"],
    "slack":       ["cmd.exe", "/c", "start", "slack"],
}

def open_browser_url(url: str):
    """Abre una URL en el navegador predeterminado de forma segura."""
    # Validar que sea una URL real, no una inyección de comandos
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    # Usamos subprocess.Popen con lista de argumentos (sin shell=True)
    subprocess.Popen(["cmd.exe", "/c", "start", "", url], shell=False)
    return True

# =================================================================
# ENDPOINTS
# =================================================================

try:
    import psutil # type: ignore
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

@app.route('/api/system/processes', methods=['GET'])
@require_api_key
def get_processes():
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "STATUS eq RUNNING"],
            capture_output=True, text=True, timeout=10, shell=False
        )
        return jsonify({"status": "success", "data": result.stdout[:1000]}), 200  # type: ignore
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/system/health', methods=['GET'])
@require_api_key
def get_health():
    """Retorna métricas de salud del sistema (CPU, RAM, Disco)"""
    resp = {
        "status": "success",
        "data": {
            "cpu": "N/A",
            "ram": "N/A",
            "disk": "N/A"
        }
    }

    if not PSUTIL_AVAILABLE:
        # Permite que el health check pase pero indica que psutil falta
        resp["message"] = "psutil no está disponible (algunas métricas faltarán)"
        return jsonify(resp), 200
    
    try:
        cpu = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resp["data"] = {
            "cpu": f"{cpu}%",
            "ram": f"{memory.percent}%",
            "disk": f"{disk.percent}%",
            "ram_used": f"{round(memory.used / (1024**3), 2)}GB",
            "ram_total": f"{round(memory.total / (1024**3), 2)}GB"
        }
        return jsonify(resp), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/pc/action', methods=['POST'])
@require_api_key
def pc_action():
    """Ejecuta aplicaciones de forma segura usando allowlist estricta."""
    data = request.json or {}
    action = data.get("action", "").lower().strip()

    # --- Búsqueda en buscadores web ---
    if action.startswith("search:"):
        parts = action.split(":", 2)
        if len(parts) >= 3:
            engine = parts[1].lower().strip()
            query = urllib.parse.quote(parts[2].strip())
            urls = {
                "youtube": f"https://www.youtube.com/results?search_query={query}",
                "chatgpt": f"https://chatgpt.com/?q={query}",
                "google":  f"https://www.google.com/search?q={query}",
            }
            url = urls.get(engine, urls["google"])
            if open_browser_url(url):
                return jsonify({"status": "success", "message": f"Búsqueda en {engine}: {parts[2].strip()}"}), 200
        return jsonify({"status": "error", "message": "Formato de búsqueda inválido."}), 400

    # --- Reproducción de música en YouTube ---
    if action.startswith("play:"):
        song = action[5:].strip()  # type: ignore
        if not song:
            return jsonify({"status": "error", "message": "No se especificó canción."}), 400
        query = urllib.parse.quote(song)
        url = f"https://www.youtube.com/results?search_query={query}"
        if open_browser_url(url):
            return jsonify({"status": "success", "message": f"Reproduciendo: {song}"}), 200

    # --- Apertura de apps usando allowlist estricta ---
    if action.startswith("open:"):
        app_name = action[5:].strip()  # type: ignore
        # Buscar en allowlist (coincidencia exacta o contenida)
        cmd_args = None
        for key, args in APP_ALLOWLIST.items():
            if key in app_name:
                cmd_args = args
                break
        if cmd_args:
            try:
                subprocess.Popen(cmd_args, shell=False)  # type: ignore
                return jsonify({"status": "success", "message": f"Abriendo: {app_name}"}), 200
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        else:
            return jsonify({"status": "error", "message": f"Aplicación '{app_name}' no está en la lista permitida."}), 403

    # --- Acciones directas del allowlist ---
    cmd_args = APP_ALLOWLIST.get(action)
    if cmd_args:
        try:
            subprocess.Popen(cmd_args, shell=False)
            return jsonify({"status": "success", "message": f"Se ejecutó: {action}"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": f"Acción '{action}' no reconocida o no permitida."}), 400


@app.route('/api/pc/mouse', methods=['POST'])
@require_api_key
def pc_mouse():
    """Control de Mouse"""
    if not PYAUTOGUI_AVAILABLE:
        return jsonify({"status": "error", "message": "PyAutoGUI no está disponible"}), 501

    data = request.json or {}
    action = data.get("action")
    x = data.get("x")
    y = data.get("y")

    try:
        if action == "move_to" and x is not None and y is not None:
            pyautogui.moveTo(int(x), int(y), duration=0.2)
        elif action == "click":
            if x is not None and y is not None:
                pyautogui.click(x=int(x), y=int(y))
            else:
                pyautogui.click()
        elif action == "double_click":
            pyautogui.doubleClick()
        elif action == "right_click":
            pyautogui.rightClick()
        else:
            return jsonify({"status": "error", "message": "Acción de mouse no válida"}), 400

        return jsonify({"status": "success", "message": f"{action} realizado"}), 200
    except pyautogui.FailSafeException:
        return jsonify({"status": "aborted", "message": "FailSafe activado: mouse en esquina de pantalla. Acción cancelada."}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/pc/keyboard', methods=['POST'])
@require_api_key
def pc_keyboard():
    """Control de Teclado"""
    if not PYAUTOGUI_AVAILABLE:
        return jsonify({"status": "error", "message": "PyAutoGUI no está disponible"}), 501

    data = request.json or {}
    action = data.get("action")
    text = data.get("text")
    keys = data.get("keys", [])

    try:
        if action == "type" and text:
            pyautogui.write(str(text), interval=0.01)
        elif action == "press" and text:
            pyautogui.press(str(text))
        elif action == "hotkey" and keys:
            pyautogui.hotkey(*[str(k) for k in keys])
        else:
            return jsonify({"status": "error", "message": "Acción de teclado no válida"}), 400

        return jsonify({"status": "success", "message": f"Teclado: {action} ejecutado"}), 200
    except pyautogui.FailSafeException:
        return jsonify({"status": "aborted", "message": "FailSafe activado: mouse en esquina de pantalla. Acción cancelada."}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/vision/screenshot', methods=['GET'])
@require_api_key
def get_screenshot():
    """Retorna Base64 de la pantalla"""
    if not PYAUTOGUI_AVAILABLE:
        return jsonify({"status": "error", "message": "PyAutoGUI no está disponible"}), 501

    try:
        temp_path = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'vision_temp.jpg')
        screenshot = pyautogui.screenshot()
        if screenshot.mode != 'RGB':
            screenshot = screenshot.convert('RGB')
        screenshot.thumbnail((1280, 1280))
        screenshot.save(temp_path, format="JPEG", quality=75)

        with open(temp_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        os.remove(temp_path)

        return jsonify({
            "status": "success",
            "image_base64": f"data:image/jpeg;base64,{encoded_string}"
        }), 200
    except pyautogui.FailSafeException:
        return jsonify({"status": "aborted", "message": "FailSafe activado."}), 409
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("=========================================")
    print("[START] WINDOWS TOOL SERVER - ZODIT GOLD v3.1 ")
    print("=========================================")
    print(f"[STATUS] PyAutoGUI: {'ACTIVO (FailSafe=ON)' if PYAUTOGUI_AVAILABLE else 'INACTIVO'}")
    print("[AUTH] API Key: CONFIGURADA (obligatoria)")
    print(f"[NET] API Corriendo en: http://0.0.0.0:{PORT_TOOLS}")
    print("=========================================")
    app.run(host='0.0.0.0', port=PORT_TOOLS, threaded=True)
