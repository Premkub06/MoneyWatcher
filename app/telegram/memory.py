"""
In-memory per-chat conversation history.
Resets on restart — acceptable for a personal single-user bot.
"""

MAX_TURNS = 20  # keep last N (role, text) turns per chat, older ones dropped

_history: dict[int, list[dict]] = {}


def get_history(chat_id: int) -> list[dict]:
    """Get conversation history for a chat as a list of {role, text} dicts."""
    return _history.get(chat_id, [])


def append(chat_id: int, role: str, text: str) -> None:
    """Append a turn to a chat's history, trimming to MAX_TURNS."""
    turns = _history.setdefault(chat_id, [])
    turns.append({"role": role, "text": text})
    if len(turns) > MAX_TURNS:
        del turns[: len(turns) - MAX_TURNS]


def clear(chat_id: int) -> None:
    """Clear a chat's history."""
    _history.pop(chat_id, None)
