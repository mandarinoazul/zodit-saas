import time
from datetime import datetime, timedelta
from typing import Any, Dict


# Estado de sesión en memoria para cada remitente (sender).
session_contexts: Dict[str, Dict[str, Any]] = {}


def get_session(sender: str) -> Dict[str, Any]:
    """Obtiene (o crea) el contexto de sesión para un sender dado."""
    if sender not in session_contexts:
        session_contexts[sender] = {
            "last_contact": "",
            "last_phone": "",
            "last_body": "",
            "last_intent": "",
            "last_rag": "",
            "pending_msg": None,
            "history": [],  # [{role: user|assistant, content: text}]
        }
    ctx = session_contexts[sender]
    ctx["_last_seen"] = datetime.utcnow()
    return ctx


def save_session(sender: str, history_limit: int = 6, **kwargs: Any) -> None:
    """Actualiza campos del contexto de sesión y mantiene el historial acotado."""
    ctx = get_session(sender)
    for k, v in kwargs.items():
        if v is None:
            continue
        if k == "history_append":
            ctx.setdefault("history", [])
            ctx["history"].append(v)
            ctx["history"] = ctx["history"][-history_limit * 2 :]
        else:
            ctx[k] = str(v)
    ctx["_last_seen"] = datetime.utcnow()


def prune_sessions(max_age_minutes: int = 60 * 24, max_sessions: int = 1000) -> None:
    """
    Elimina sesiones huérfanas en memoria:
    - Por tiempo de inactividad (max_age_minutes).
    - Por límite duro de cantidad de sesiones (max_sessions).
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=max_age_minutes)

    # Borrar por TTL
    to_delete = []
    for sender, ctx in session_contexts.items():
        last_seen = ctx.get("_last_seen")
        if isinstance(last_seen, datetime) and last_seen < cutoff:
            to_delete.append(sender)
    for sender in to_delete:
        session_contexts.pop(sender, None)

    # Si aún hay demasiadas sesiones, eliminar las más antiguas
    if len(session_contexts) > max_sessions:
        sorted_items = sorted(
            session_contexts.items(),
            key=lambda item: item[1].get("_last_seen", datetime.utcnow()),
        )
        overflow = len(session_contexts) - max_sessions
        for sender, _ in sorted_items[:overflow]:
            session_contexts.pop(sender, None)

