from ai.ollama_client import ask_ollama
from ai.prompts import COMMAND_PROMPT
from ai.prompts import CHAT_PROMPT


def ask_ai(query, context, os_type):

    query_lower = query.lower()

    # words that indicate explanation / conversation
    question_words = [
        "what", "why", "how", "explain",
        "describe", "example", "list",
        "difference", "meaning"
    ]

    is_question = any(word in query_lower for word in question_words)

    # -------------------------
    # CHAT MODE
    # -------------------------
    if is_question:

        prompt = CHAT_PROMPT
        prompt = prompt.replace("{query}", query)
        prompt = prompt.replace("{context}", context)
        prompt = prompt.replace("{os}", os_type)

        return ask_ollama(prompt, mode="chat")

    # -------------------------
    # COMMAND MODE
    # -------------------------
    else:

        prompt = COMMAND_PROMPT
        prompt = prompt.replace("{query}", query)
        prompt = prompt.replace("{context}", context)
        prompt = prompt.replace("{os}", os_type)

        return ask_ollama(prompt, mode="command")