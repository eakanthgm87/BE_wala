import time

from ai.ai_engine import ask_ai
from context.detector import detect_context
from core.os_detect import get_os

from chatbot.chat_memory import (
    add_user_message,
    add_ai_message,
    format_history
)

from chatbot.response_cleaner import clean_response
from chatbot.project_explainer import (
    explain_project,
    explain_file,
    review_file,
    generate_readme
)


# --------------------------------------------------
# Typing animation for realistic AI output
# --------------------------------------------------

def type_print(text, speed=0.004):

    for char in text:
        print(char, end="", flush=True)
        time.sleep(speed)

    print("\n")


# --------------------------------------------------
# Prompt Builder (ChatGPT style responses)
# --------------------------------------------------

def build_prompt(user_message):

    history = format_history()

    context = detect_context()
    os_type = get_os()

    prompt = f"""
You are ShellMind AI, an advanced developer assistant similar to ChatGPT.

Your job is to explain concepts clearly and thoroughly.

System Context:
Operating System: {os_type}
Project Context: {context}

Conversation History:
{history}

User Question:
{user_message}

You MUST structure every answer like this:

### 1. Definition
Explain the concept clearly.

### 2. Detailed Explanation
Explain how it works and why it is important.

### 3. Example
Provide a practical example or code snippet.

### 4. Key Points
Provide bullet points of important ideas.

### 5. Simple Summary
Explain the concept in simple terms.

Rules:
- Responses must be detailed.
- Do not give one-line answers.
- Always include examples when possible.
- Do not wrap the response in quotes.
- Use clean formatting.
"""

    return prompt


# --------------------------------------------------
# Ask AI with context + memory
# --------------------------------------------------

def ask_chatbot(message):

    add_user_message(message)

    prompt = build_prompt(message)

    response = ask_ai(prompt, detect_context(), get_os())

    response = clean_response(response)

    # If response too short, ask AI to expand
    if len(response.split()) < 30:

        expand_prompt = f"""
Expand the following answer with explanation and examples:

{response}
"""

        response = ask_ai(expand_prompt, detect_context(), get_os())
        response = clean_response(response)

    add_ai_message(response)

    return response


# --------------------------------------------------
# Command Parser
# --------------------------------------------------

def handle_special_commands(user_msg):

    msg = user_msg.lower()

    if "explain project" in msg:
        return explain_project()

    if msg.startswith("explain file"):

        parts = user_msg.split(" ", 2)

        if len(parts) < 3:
            return "Usage: explain file <path>"

        return explain_file(parts[2])

    if msg.startswith("review file"):

        parts = user_msg.split(" ", 2)

        if len(parts) < 3:
            return "Usage: review file <path>"

        return review_file(parts[2])

    if "generate readme" in msg:
        return generate_readme()

    return None


# --------------------------------------------------
# Chat Mode
# --------------------------------------------------

def start_chat():

    print("\n════════════════════════════════════")
    print("🤖 ShellMind AI Chat Mode")
    print("Type 'exit' to leave chat")
    print("════════════════════════════════════\n")

    while True:

        user_msg = input("You > ").strip()

        if not user_msg:
            continue

        if user_msg.lower() in ["exit", "quit"]:
            print("\n👋 Leaving chat mode.\n")
            break

        # --------------------------------
        # Special AI commands
        # --------------------------------

        command_result = handle_special_commands(user_msg)

        if command_result:

            print("══════════════════════════════")
            print("🤖 ShellMind AI")
            print("══════════════════════════════")

            type_print(command_result)

            print("══════════════════════════════\n")

            continue

        # --------------------------------
        # Normal AI conversation
        # --------------------------------

        print("\n🤖 Thinking...\n")

        response = ask_chatbot(user_msg)

        print("══════════════════════════════")
        print("🤖 ShellMind AI")
        print("══════════════════════════════")

        type_print(response)

        print("══════════════════════════════\n")