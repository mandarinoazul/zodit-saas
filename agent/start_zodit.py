import subprocess
import time
import os
import sys
import signal
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

# =================================================================
# ZODIT GOLD v3.3 - CROSS-PLATFORM MASTER LAUNCHER
# =================================================================

BASE_DIR   = Path(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = BASE_DIR / "skills" / "sales-assistant"
SCRIPTS_DIR = SKILLS_DIR / "scripts"

load_dotenv(BASE_DIR / ".env")

PORT_WHATSAPP  = int(os.getenv("PORT_WHATSAPP",  3001))
PORT_DASHBOARD = int(os.getenv("PORT_DASHBOARD", 5001))
ZODIT_API_KEY  = os.getenv("ZODIT_API_KEY", "CHANGE_ME")

child_processes: list[subprocess.Popen] = []

def spawn(name: str, cmd_list: list[str], description: str) -> subprocess.Popen | None:
    print(f"   → {description}...")
    try:
        custom_env = os.environ.copy()
        custom_env["PYTHONIOENCODING"] = "utf-8"
        # Ensure node and python are in path
        proc = subprocess.Popen(cmd_list, shell=False, env=custom_env)
        return proc
    except Exception as e:
        print(f"   ❌ Error iniciando {name}: {e}")
        return None

def kill_port_process(port: int) -> None:
    if os.name == 'nt': # Windows
        try:
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, shell=False)
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.split()[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, shell=False)
        except: pass
    else: # Linux/Mac (Docker)
        try:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, shell=False)
        except: pass

def shutdown_all() -> None:
    print("\n🛑 Apagando servicios...")
    for p in child_processes:
        try: p.terminate()
        except: pass
    time.sleep(1)
    for p in child_processes:
        try: 
            if p.poll() is None: p.kill()
        except: pass

def launch() -> None:
    print(f"\n🚀 INICIANDO ZODIT GOLD v3.3 ({'Windows' if os.name == 'nt' else 'Linux/Docker'})\n")
    for port in [5000, 5001, 8001, 3001]: kill_port_process(port)
    
    # Detectar ejecutable de python
    if os.name == 'nt':
        python_exe = os.path.join(str(BASE_DIR), "venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = sys.executable
    else:
        python_exe = sys.executable

    service_defs = [
        ("WS-Session",  ["node", str(SCRIPTS_DIR / "whatsapp_service.js")], "WhatsApp Bridge"),
        ("Jarvis-Core", [python_exe, str(BASE_DIR / "jarvis_core.py")], "JARVIS Core"),
        ("Dashboard",   [python_exe, str(SCRIPTS_DIR / "dashboard.py")], "Dashboard Web")
    ]

    for name, cmd, desc in service_defs:
        p = spawn(name, cmd, desc)
        if p: child_processes.append(p)
        time.sleep(2)

    print("\n✅ Sistema Operativo. Ctrl+C para salir.\n")

if __name__ == "__main__":
    try:
        launch()
        # Mapeo para reinicio
        if os.name == 'nt':
            python_exe = os.path.join(str(BASE_DIR), "venv", "Scripts", "python.exe")
            if not os.path.exists(python_exe): python_exe = sys.executable
        else:
            python_exe = sys.executable

        service_cmds = {
            "WS-Session":  ["node", str(SCRIPTS_DIR / "whatsapp_service.js")],
            "Jarvis-Core": [python_exe, str(BASE_DIR / "jarvis_core.py")],
            "Dashboard":   [python_exe, str(SCRIPTS_DIR / "dashboard.py")]
        }

        while True:
            time.sleep(5)
            for i, p in enumerate(child_processes):
                if p.poll() is not None:
                    # Identificar servicio por argumentos
                    name = "Unknown"
                    for n, cmd in service_cmds.items():
                        if all(c in p.args for c in cmd): 
                            name = n
                            break
                    print(f"⚠️  [{name}] se detuvo. Reiniciando...")
                    new_p = spawn(name, service_cmds.get(name, p.args), f"Respawning {name}")
                    if new_p: child_processes[i] = new_p
    except KeyboardInterrupt: pass
    finally: shutdown_all()