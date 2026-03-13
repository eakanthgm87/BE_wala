def clean_response(text):

    if not text:
        return text

    text = text.strip()

    if text.startswith("echo"):
        text = text.replace("echo", "").strip()

    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]

    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1]

    return text