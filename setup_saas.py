import os
import sys
import subprocess
import secrets

def print_banner():
    print("="*60)
    print("      ZODIT GOLD - ONE-CLICK SMART SETUP (UNIVERSAL)")
    print("="*60)

def check_dependencies():
    # Detect folders
    is_root = os.path.exists("agent")
    work_dir = "agent" if is_root else "."
    
    # Python Deps
    deps = ["flask", "fastapi", "uvicorn", "httpx", "psutil", "slowapi", "python-dotenv", "pyautogui", "flask-cors"]
    print(f"\n📦 [Python] Instalando dependencias en {work_dir}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + deps)
        print("✅ Python: OK")
    except Exception as e:
        print(f"❌ Error Python: {e}")

    # Node Deps
    if os.path.exists(os.path.join(work_dir, "package.json")):
        print("\n📦 [Node.js] Verificando dependencias...")
        try:
            cwd = os.path.abspath(work_dir)
            subprocess.check_call(["npm", "install"], shell=True, cwd=cwd)
            print("✅ Node.js: OK")
        except Exception as e:
            print("⚠️ Nota: Asegúrate de tener Node.js instalado para WhatsApp.")

def verify_env():
    is_root = os.path.exists("agent")
    env_path = "agent/.env" if is_root else ".env"
    
    print(f"\n[2/3] Verificando {env_path}...")
    if not os.path.exists(env_path):
        master_key = secrets.token_urlsafe(32)
        with open(env_path, "w") as f:
            f.write(f"ZODIT_API_KEY={master_key}\n")
            f.write("PORT_WHATSAPP=3001\n")
            f.write("PORT_GATEWAY=8001\n")
            f.write("PREFERRED_MODEL=llama3.1:8b\n")
        print(f"✅ .env creado con LLAVE MAESTRA: {master_key}")
    else:
        print("✅ Configuración detectada.")

def launch():
    is_root = os.path.exists("agent")
    script = "agent/start_zodit.py" if is_root else "start_zodit.py"
    cwd = "agent" if is_root else "."
    
    print("\n[3/3] Iniciando el Ecosistema ZODIT...")
    print("="*60)
    try:
        # Launch start_zodit.py in a new console
        subprocess.Popen([sys.executable, "start_zodit.py"], 
                         cwd=os.path.abspath(cwd),
                         creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        print("\n🚀 ¡NÚCLEO ACTIVO!")
        print(f"\nTu servidor local está corriendo en el puerto 8001.")
        print("Recuerda abrir otra terminal y activar tu túnel de Cloudflare.")
        print("\n" + "="*60)
    except Exception as e:
        print(f"❌ Error al lanzar: {e}")

if __name__ == "__main__":
    print_banner()
    check_dependencies()
    verify_env()
    launch()
    input("\nPresiona Enter para finalizar...")
