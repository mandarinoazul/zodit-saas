import re
from typing import Dict, List

from session_manager import get_session


# =================================================================
# NLU & REGEX UTILITIES (extraído de main_agent.py)
# =================================================================

SEND_VERBS_RE = re.compile(
    r"\b(?:dile?|avisa|tira|manda|envia|cuenta|pasa|suelta|notifica|escribe)\b",
    re.I,
)
REROUTE_RE = re.compile(
    r"\b(?:envia|manda|diselo|pasa)\s+al\s+(?:numero\s+de|contacto\s+de)?\s*(?P<contact>[\w\s]{2,30})",
    re.I,
)
SEND_TO_NAME_RE = re.compile(
    r"(?:"
    + SEND_VERBS_RE.pattern
    + r")\s+a\s+(?:el|la)?\s*(?P<contact>[\w\s]{2,25}?)\s+que\s+(?P<body>.+)",
    re.I,
)
SEND_TO_NAME_COLON_RE = re.compile(
    r"(?:"
    + SEND_VERBS_RE.pattern
    + r")\s+a\s+(?:el|la)?\s*(?P<contact>[\w\s]{2,25?}?)[,:\s]+(?P<body>[^:].{5,})",
    re.I,
)
SEND_DICIENDO_RE = re.compile(
    r"(?:"
    + SEND_VERBS_RE.pattern
    + r")\s+a\s+(?P<contact>[\w\s]{2,25}?)\s+(?:diciendo|para\s+que\s+le\s+digas)\s+(?P<body>.+)",
    re.I,
)
SEND_NO_CONTACT_RE = re.compile(
    r"(?:"
    + SEND_VERBS_RE.pattern
    + r")\s+(?:un\s+)?(?:mensaje\s+)?(?:para\s+|que\s+diga\s+|diciendo\s+)?(?P<body>.{4,})",
    re.I,
)

PC_PATTERNS = {
    "calc": re.compile(r"\b(?:calculadora)\b", re.I),
    "screenshot": re.compile(
        r"\b(?:captura|screenshot|foto|ves|pantalla|analiza)\b",
        re.I,
    ),
    "processes": re.compile(r"\b(?:procesos|tasks)\b", re.I),
    "help": re.compile(
        r"\b(?:ayuda|comandos|instrucciones|qué\s+puedes\s+hacer)\b",
        re.I,
    ),
}
PC_OPEN_RE = re.compile(
    r"\b(?:abre|lanza)\s+(?:el\s+|la\s+)?(?P<app>[\w\s\.\-]{2,40})",
    re.I,
)
PC_SEARCH_RE = re.compile(
    r"\b(?:busca\s+en\s+(?P<engine>youtube|google|chatgpt))(?:\s+)?(?P<query>.+)",
    re.I,
)
PC_MUSIC_RE = re.compile(
    r"\b(?:pon|reproduce|toca|escuchar)\s+(?P<song>.+)",
    re.I,
)


def parse_send_commands(text: str, sender: str) -> List[Dict]:
    """Extrae comandos de envío de mensajes a contactos desde texto libre."""
    ctx = get_session(sender)
    results: List[Dict] = []
    for m in REROUTE_RE.finditer(text):
        results.append(
            {
                "contact": m.group("contact").strip().title(),
                "body": ctx.get("last_body", ""),
                "is_reroute": True,
            }
        )
    for m in SEND_TO_NAME_RE.finditer(text):
        results.append(
            {
                "contact": m.group("contact").strip().title(),
                "body": m.group("body").strip(),
                "is_reroute": False,
            }
        )
    for m in SEND_TO_NAME_COLON_RE.finditer(text):
        results.append(
            {
                "contact": m.group("contact").strip().title(),
                "body": m.group("body").strip(),
                "is_reroute": False,
            }
        )
    if not results and SEND_VERBS_RE.search(text):
        m = SEND_DICIENDO_RE.search(text) or SEND_NO_CONTACT_RE.search(text)
        if m:
            contact = (
                m.group("contact").strip().title()
                if "contact" in m.groupdict()
                else ctx.get("last_contact")
            )
            results.append(
                {
                    "contact": contact,
                    "body": m.group("body").strip(),
                    "is_reroute": False,
                }
            )
    return results


def detect_pc_commands(text: str) -> List[str]:
    """Detecta comandos de control de PC desde lenguaje natural."""
    commands: List[str] = []
    for m in PC_SEARCH_RE.finditer(text):
        commands.append(f"search:{m.group('engine')}:{m.group('query')}")
    for k, v in PC_PATTERNS.items():
        if v.search(text):
            commands.append(k)
    for m in PC_MUSIC_RE.finditer(text):
        commands.append(f"play:{m.group('song')}")
    for m in PC_OPEN_RE.finditer(text):
        commands.append(f"open:{m.group('app').strip().lower()}")
    return commands


def extract_phone_number(text: str) -> str | None:
    """Extrae un número de teléfono de un texto arbitrario."""
    labeled = re.search(
        r"(?:tel|num|cel|whatsapp)[\s:=]*(\+?[\d][\d\s\-\.]{5,17}[\d])",
        text,
        re.I,
    )
    if labeled:
        return re.sub(r"[^\d\+]", "", labeled.group(1))
    standalones = re.findall(r"\+?\d[\d\s\-\.]{7,16}\d", text)
    for m in standalones:
        digits = re.sub(r"[^\d\+]", "", m)
        if 9 <= len(digits) <= 15:
            return digits
    return None

