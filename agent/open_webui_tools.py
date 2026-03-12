"""
title: Windows Tool Server Bridge
author: Agent Builder (Zodit/Mandarino)
version: 1.0.0
description: Conjunto de herramientas (Tools/Skills) para Open WebUI. Permiten a modelos como Qwen2.5:3b controlar el PC Host (Windows) a través de peticiones HTTP al Tool Server.
"""

import urllib.request
import json
import logging
import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Intentar cargar .env si existe en el mismo directorio que el script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

ZODIT_API_KEY = os.getenv("ZODIT_API_KEY", "")

# URL del servidor backend en Windows
PORT_TOOLS = os.getenv("PORT_TOOLS", "5005")
TOOL_SERVER_URL = os.getenv("TOOL_SERVER_URL", f"http://127.0.0.1:{PORT_TOOLS}")

class Tools:
    def __init__(self):
        # Configuracion de auth centralizada
        self.headers = {'Content-Type': 'application/json'}
        if Z_KEY := os.getenv("ZODIT_API_KEY"):
            self.headers['X-API-Key'] = Z_KEY

    def get_windows_processes(self) -> str:
        """
        You MUST call this tool when the user asks to see what programs, apps, or tasks are currently running on their computer.
        It returns a list of active Windows processes.
        """
        try:
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/system/processes", headers=self.headers, method="GET")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    data = result.get("data", "")
                    return f"Active Processes:\n{data}\n\nINSTRUCTION: Formatea esto en una lista amigable para el usuario y mencione que estos son los programas corriendo actualmente."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to reach the Windows Tool Server. Ensure tool_server.py is running on port 5005. Error: {str(e)}"

    def open_application(self, app_name: str) -> str:
        """
        You MUST call this tool when the user asks you to open, start, or launch an application or program on their computer.
        
        :param app_name: The name of the application to open (e.g., "calculadora", "chrome", "opera", "notepad", "discord", "word", "excel").
        """
        try:
            data = json.dumps({"action": f"open:{app_name}"}).encode('utf-8')
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/pc/action", data=data, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    return f"Success: Application '{app_name}' was opened on the host PC.\n\nINSTRUCTION: Confirma al usuario con un tono amigable que has abierto la aplicación."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to execute command on Host. Error: {str(e)}"

    def simulate_keyboard_type(self, text_to_type: str) -> str:
        """
        You MUST call this tool to type text onto the user's screen automatically using their keyboard.
        Use this when the user specifically asks you to "type" something, "write" something on the screen.
        
        :param text_to_type: The exact string of text to type out via the simulated keyboard.
        """
        try:
            data = json.dumps({"action": "type", "text": text_to_type}).encode('utf-8')
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/pc/keyboard", data=data, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    return f"Success: Typed '{text_to_type}' on the host PC.\n\nINSTRUCTION: Confirma brevemente al usuario que escribiste el texto en su pantalla."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to simulate keyboard. Error: {str(e)}"

    def simulate_keyboard_press(self, key: str) -> str:
        """
        You MUST call this tool to press a specific key on the user's keyboard (like 'enter', 'tab', 'win', 'space', 'backspace').
        
        :param key: The exact key name to press (e.g., 'enter', 'esc', 'win').
        """
        try:
            data = json.dumps({"action": "press", "text": key.lower()}).encode('utf-8')
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/pc/keyboard", data=data, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    return f"Success: Pressed '{key}' on the keyboard."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to press key. Error: {str(e)}"

    def simulate_mouse_click(self, action: str, x: int = 0, y: int = 0) -> str:
        """
        You MUST call this tool when the user asks you to click on something.
        
        :param action: The type of click (e.g., 'click', 'double_click', 'right_click').
        :param x: (Optional) The X coordinate on the screen.
        :param y: (Optional) The Y coordinate on the screen.
        """
        try:
            if x is not None and y is not None and x != 0 and y != 0:
                data = {"action": action, "x": int(x), "y": int(y)}
            else:
                data = {"action": action}
                
            req_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/pc/mouse", data=req_data, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    return f"Success: Mouse action '{action}' performed."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to simulate mouse. Error: {str(e)}"

    def get_screen_context(self) -> str:
        """
        You MUST call this tool when you need to SEE what is currently on the user's screen. 
        It returns a base64 encoded screenshot of the host PC. 
        Use this when the user says "what do you see?", "what's on my screen?", or when you need visual context to decide where to click.
        """
        try:
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/vision/screenshot", headers=self.headers, method="GET")
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    b64 = result.get("image_base64", "")
                    return f"Screenshot captured globally. The image is included below.\n\n![Screenshot]({b64})\n\nCRITICAL INSTRUCTION: Analyze the image above very carefully. Tell the user EXACTLY what you see on their screen right now."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to get screenshot. Error: {str(e)}"

    def browse_web_search(self, engine: str, query: str) -> str:
        """
        You MUST call this tool when the user asks you to search for something on the web, on YouTube, or on ChatGPT.
        
        :param engine: The search engine to use ('google', 'youtube', or 'chatgpt').
        :param query: The search query (what the user wants to search for).
        """
        try:
            data = json.dumps({"action": f"search:{engine.lower()}:{query}"}).encode('utf-8')
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/pc/action", data=data, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    return f"Success: Searched for '{query}' on {engine.capitalize()}.\n\nINSTRUCTION: Confirma al usuario que has abierto el navegador para buscar su consulta."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to search the web. Error: {str(e)}"

    def play_music_youtube(self, song_name: str) -> str:
        """
        You MUST call this tool when the user explicitly asks you to PLAY a song, put on some music, or listen to a track on YouTube.
        
        :param song_name: The name of the song and/or artist (e.g., "Bohemian Rhapsody Queen").
        """
        try:
            data = json.dumps({"action": f"play:{song_name}"}).encode('utf-8')
            req = urllib.request.Request(f"{TOOL_SERVER_URL}/api/pc/action", data=data, headers=self.headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get("status") == "success":
                    return f"Success: Opening YouTube to play '{song_name}'.\n\nINSTRUCTION: Dile al usuario que estás poniendo la canción en YouTube de forma entusiasta."
                return f"Error from Host: {result.get('message')}"
        except Exception as e:
            return f"System Error: Failed to play music. Error: {str(e)}"
