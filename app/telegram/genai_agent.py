import os

from google import genai
from google.genai import types

from app.telegram import memory
from app.telegram.tools import TOOL_DECLARATIONS, TOOL_FUNCTIONS

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_TOOL_ITERATIONS = 5

SYSTEM_INSTRUCTION = (
    "You are a personal finance assistant for the MoneyWatcher app. "
    "Use the provided tools to answer questions about balances, transactions, and categories. "
    "You can discuss money strategy and budgeting, but you can never update a balance yourself — "
    "tell the user to use /balance <provider> <amount> for that. Keep replies short, plain text (Telegram)."
)

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
    return _client


def _history_to_contents(chat_id: int) -> list[types.Content]:
    contents = []
    for turn in memory.get_history(chat_id):
        role = "model" if turn["role"] == "model" else "user"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn["text"])]))
    return contents


async def _call_tool(name: str, args: dict):
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return {"error": f"unknown tool '{name}'"}
    result = func(**args)
    if hasattr(result, "__await__"):
        result = await result
    return result


async def chat(chat_id: int, user_text: str) -> str:
    """Run one chat turn: send user_text + history to Gemini, resolve tool calls, return the final reply text."""
    client = _get_client()
    contents = _history_to_contents(chat_id)
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))

    config = types.GenerateContentConfig(
        tools=TOOL_DECLARATIONS,
        system_instruction=SYSTEM_INSTRUCTION,
    )

    reply_text = "Sorry, I couldn't come up with a reply."
    for _ in range(MAX_TOOL_ITERATIONS):
        response = await client.aio.models.generate_content(model=MODEL, contents=contents, config=config)
        candidate = response.candidates[0]
        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]

        if not function_calls:
            reply_text = response.text or reply_text
            break

        contents.append(candidate.content)
        response_parts = []
        for fc in function_calls:
            try:
                result = await _call_tool(fc.name, dict(fc.args or {}))
            except Exception as e:
                result = {"error": str(e)}
            response_parts.append(types.Part.from_function_response(name=fc.name, response={"result": result}))
        contents.append(types.Content(role="tool", parts=response_parts))
    else:
        reply_text = "I couldn't finish looking that up in time — try asking again, maybe more specifically."

    memory.append(chat_id, "user", user_text)
    memory.append(chat_id, "model", reply_text)
    return reply_text
