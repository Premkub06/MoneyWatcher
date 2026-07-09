import os


def is_authorized(chat_id: int) -> bool:
    """Only the owner's chat_id (USER_TOKEN) may talk to this bot."""
    user_token = os.getenv("USER_TOKEN", "")
    return user_token != "" and str(chat_id) == user_token
