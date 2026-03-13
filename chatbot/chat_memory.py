# Handles conversation memory

chat_history = []
MAX_HISTORY = 20


def add_user_message(message):
    chat_history.append({"role": "user", "content": message})


def add_ai_message(message):
    chat_history.append({"role": "assistant", "content": message})


def clear_history():
    chat_history.clear()


def get_history():
    return chat_history


def format_history():
    """
    Convert history into a readable prompt format
    """
    formatted = ""
    for msg in chat_history[-MAX_HISTORY:]:
        formatted += f'{msg["role"]}: {msg["content"]}\n'
    return formatted


def summarize_history():
    """
    Simple summarization if history gets large
    """
    if len(chat_history) < MAX_HISTORY:
        return format_history()

    summary = ""
    for msg in chat_history[-5:]:
        summary += msg["content"][:120] + "\n"

    return summary