# 👑 ZODIT GOLD: Manual Maestro de Operaciones (ROOT)

Este es el único manual que necesitas para iniciar todo el ecosistema.

---

## 🚀 Inicio en 2 Pasos (Literalmente)

### 1. Preparación Total
1. Abre una terminal en la raíz del proyecto (`zodit-saas-monorepo`).
2. Ejecuta: `python setup_saas.py`
   > [!IMPORTANT]
   > El script instalará todo por ti, configurará tu PC y abrirá la consola de JARVIS automáticamente.

### 2. El Puente Neural (Cloudflare)
1. Inicia sesión (Solo la primera vez): `cloudflared tunnel login`
2. Inicia el túnel: `cloudflared tunnel run --url http://localhost:8001 zodit`
   *(Si el túnel no existe, ejecuta `cloudflared tunnel create zodit` primero).*

---

## 🔐 Configuración Web (Vercel)
Configura estas variables en tu panel de Vercel:
- `NEXT_PUBLIC_GATEWAY_URL`: `https://zodit-gateway.mandev.site`
- `NEXT_PUBLIC_GATEWAY_SECRET`: Usa la **ZODIT_API_KEY** que verás en tu archivo `agent/.env`.

---
*ZODIT Gold v4.0 - Simplificado para Daniel Cabrera.*
