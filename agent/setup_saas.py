import os
import sys
import subprocess
import time
from pathlib import Path

def print_banner():
    print("="*60)
    print("      ZODIT GOLD - ONE-CLICK SMART SETUP")
    print("="*60)
    print("\n[1/3] Verificando entorno de Python...")

def check_dependencies():
    # Python Deps
    deps = ["flask", "fastapi", "uvicorn", "httpx", "psutil", "slowapi", "python-dotenv", "pyautogui"]
    print(f"📦 [Python] Instalando dependencias: {', '.join(deps)}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + deps)
        print("✅ Python: OK")
    except Exception as e:
        print(f"❌ Error instalando dependencias Python: {e}")

    # Node Deps
    print("\n📦 [Node.js] Verificando dependencias de WhatsApp...")
    try:
        # Check if npm is installed
        subprocess.check_call(["npm", "--version"], shell=True, stdout=subprocess.DEVNULL)
        subprocess.check_call(["npm", "install"], shell=True)
        print("✅ Node.js: OK")
    except Exception as e:
        print("⚠️  No se pudo ejecutar 'npm install'. Asegúrate de tener Node.js instalado.")
        print("   Descárgalo en: https://nodejs.org/")

def verify_env():
    print("\n[2/3] Verificando archivo de configuración (.env)...")
    if not os.path.exists(".env"):
        print("⚠️  Archivo .env no encontrado. Creando uno maestro...")
        # Generar una API Key aleatoria segura
        import secrets
        master_key = secrets.token_urlsafe(32)
        with open(".env", "w") as f:
            f.write(f"ZODIT_API_KEY={master_key}\n")
            f.write("PORT_WHATSAPP=3001\n")
            f.write("PORT_DASHBOARD=5001\n")
            f.write("PORT_GATEWAY=8001\n")
            f.write("PREFERRED_MODEL=llama3.1:8b\n")
        print(f"✅ .env creado con LLAVE MAESTRA: {master_key}")
        print("   ¡COPIA ESTA LLAVE EN VERCEL COMO 'NEXT_PUBLIC_GATEWAY_SECRET'!")
    else:
        print("✅ Configuración detectada.")

def launch():
    print("\n[3/3] Iniciando el Ecosistema ZODIT...")
    print("="*60)
    try:
        # Usar el script start_zodit.py reparado
        # En Windows, usamos 'start' para abrir el proceso en una nueva ventana si es posible, 
        # o simplemente Popen para mantenerlo en el mismo flujo.
        subprocess.Popen([sys.executable, "start_zodit.py"], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        print("\n🚀 ¡NÚCLEO ACTIVO!")
        print("\nDIRECCIÓN WEB:")
        print("🔗 https://zodit-saas.vercel.app")
        print("\nRECUERDA:")
        print("1. El túnel de Cloudflare debe estar activo.")
        print("2. Las llaves en Vercel deben coincidir con tu .env.")
        print("\n" + "="*60)
    except Exception as e:
        print(f"❌ Error al lanzar el sistema: {e}")

if __name__ == "__main__":
    print_banner()
    check_dependencies()
    verify_env()
    launch()
    print("\nPresiona Enter para cerrar esta ventana...")
    input()
