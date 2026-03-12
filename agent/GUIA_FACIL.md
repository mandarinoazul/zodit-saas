# 🌟 Guía Sencilla de Zodit Gold

¡Hola! Esta guía explica para qué sirve cada "pieza" de tu asistente de forma muy fácil, sin tecnicismos.

## 🚀 Lo que ves al ejecutar `start_zodit.py`

Cuando inicias Zodit, se encienden tres motores principales:

1.  **JARVIS Core (El Cerebro)**:
    - Es el centro de pensamiento. Aquí vive la lógica que entiende lo que dices y decide qué hacer.
2.  **WhatsApp Bridge (La Voz)**:
    - Es el "teléfono" de JARVIS. Se encarga de recibir tus mensajes de WhatsApp y enviarte las respuestas que genera el cerebro.
3.  **Tool Server (Las Herramientas)**:
    - Es el conjunto de habilidades. Piensa en esto como los "brazos" de JARVIS: aquí es donde puede ver tu pantalla, mover el mouse, buscar en internet o agendar en tu calendario.

---

## 📂 ¿Para qué sirven esos archivos extraños?

Es normal ver archivos con nombres raros. Aquí te explico los más importantes:

-   **`sessions.db` (La Memoria)**:
    - Es una pequeña base de datos donde JARVIS guarda el historial de tus conversaciones. Gracias a esto, si le dices "Recuerda lo que dije antes", él puede buscarlo aquí.
-   **`semantic_cache.json` (El Rayo ⚡)**:
    - Guarda respuestas a preguntas comunes. Si le preguntas algo que ya sabe, en lugar de "pensar" la respuesta desde cero, la saca de aquí al instante.
-   **`Prometheus` y `Grafana` (El Monitor)**:
    - Son herramientas de "salud". Sirven para ver gráficos de qué tan rápido responde JARVIS o si el servidor está muy cansado (CPU alto). No los necesitan para usar la app, son más para mantenimiento.
-   **`Docker` (La Caja Fuerte/Maleta)**:
    - Es una tecnología que permite meter toda la aplicación en una "caja" virtual. Esto sirve para que, si quieres llevarte a JARVIS a otro ordenador o a la nube, funcione exactamente igual sin tener que instalar mil cosas una por una.
-   **`.env` (El Llavero)**:
    - Aquí es donde guardamos tus llaves secretas (como la clave de WhatsApp o tu API Key). ¡Es muy importante no compartir este archivo con nadie!

---

## �️ ¿Cómo debo ejecutar JARVIS?

Esta es la duda más común. Tienes dos caminos:

### 1. El camino directo (Recomendado): `python start_zodit.py`
- **¿Qué es?**: Ejecuta JARVIS directamente en tu Windows.
- **Ventajas**: Es más rápido de iniciar, consume menos memoria y es más fácil si quieres hacer cambios rápidos en los archivos.
- **Para ti**: Si ya te funciona bien así, **sigue usando este comando**. Es el método principal para el día a día.

### 2. El camino profesional: `Docker`
- **¿Qué es?**: Ejecuta JARVIS dentro de una "burbuja" aislada.
- **Ventajas**: Es ideal si quieres dejar a JARVIS funcionando en un servidor 24/7 o si quieres usar las herramientas de monitoreo (Grafana). 
- **Cómo se usa**: Necesitas tener instalado "Docker Desktop" y ejecutar `docker-compose up -d`.

---

## 📊 ¿Qué pasa con Grafana y Prometheus?

Estas herramientas son como el **"Tablero de Control"** de un avión:

1.  **Prometheus**: Es el "recolector" de datos. Vigila cuántos mensajes envías, cuánto tarda JARVIS en pensar y si hay errores.
2.  **Grafana**: Es la "pantalla" bonita. Muestra gráficos y relojes con la información que recolectó Prometheus.

**¿Vienen con `start_zodit.py`?**
No. Estas herramientas son pesadas y solo se activan si decides usar el método de **Docker**. Para usarlas:
1.  Inicias Docker con `docker-compose up -d`.
2.  Abres en tu navegador: `http://localhost:3000` (Grafana).

**¿Son necesarias?**
No para el uso normal. Son herramientas internas para que un técnico vea el rendimiento del sistema a largo plazo. Si solo quieres hablar con JARVIS, ignóralas por ahora.

---

## �💡 Consejos Rápidos
- **Si JARVIS se confunde con la fecha**: A veces la inteligencia "cree" que vive en el año en que fue entrenada. He añadido un "Aviso de Realidad" automático para que siempre sepa que estamos en 2026.
- **Si sale un error "No LID" al enviar WhatsApp**: No te preocupes, esto es un pequeño fallo de sincronización de WhatsApp con números nuevos. Intenta enviarle un mensaje tú a ese número primero y luego pídele a JARVIS que lo haga.
- **Si el Rayo ⚡ da información vieja**: Si cambiaste de opinión sobre algo que JARVIS memorizó, he borrado el caché viejo para que empiece de cero hoy con información fresca.

¡Disfruta de tu asistente de élite! 🥂

---

## 🚀 Pruebas con Docker y start_zodit

Si ya tienes instalado **Docker Desktop** en tu PC, puedes probar el despliegue optimizado y el script de inicio rápido.

### 1. Iniciar con start_zodit.py
Este script es el "arranque inteligente" de Zodit Gold. Se encarga de verificar que Ollama y el sistema estén listos antes de levantar los servicios.

**Para probarlo:**
1. Abre una terminal (PowerShell o CMD).
2. Ejecuta:
   ```bash
   python start_zodit.py
   ```
3. El script detectará automáticamente los puertos y levantará el Gateway (8001), WhatsApp (3001) y el Dashboard (5001).

### 2. Uso con Docker (Contenedores)
El proyecto incluye un `docker-compose.yml` para facilitar el aislamiento de servicios.

**Para levantar el ecosistema en Docker:**
1. Asegúrate de que Docker Desktop esté abierto.
2. En la raíz del proyecto, ejecuta:
   ```bash
   docker-compose up -d
   ```
3. Esto levantará los servicios definidos sin interferir con tus procesos locales.
4. Para ver los logs de los contenedores:
   ```bash
   docker-compose logs -f
   ```

**¿Qué tiene Docker?**
- **Zodit Core**: El motor lógico principal.
- **WhatsApp Bridge**: El puente para mensajes.
- **Redis (opcional)**: Si el cache semántico está configurado para usar base de datos externa.

---

> [!TIP]
> Si prefieres desarrollo local rápido, usa `start_zodit.py`. Si prefieres estabilidad y aislamiento para producción personal, usa `docker-compose`.
