import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral:latest"


def ask_ollama(prompt, mode="chat"):

    try:

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": True
            },
            stream=True
        )

        full_text = ""

        for line in response.iter_lines():

            if line:
                data = json.loads(line.decode("utf-8"))

                token = data.get("response", "")
                print(token, end="", flush=True)
                full_text += token

        print()

        if mode == "command":
            match = re.search(r"`([^`]+)`", full_text)
            if match:
                return match.group(1)

            return full_text.split("\n")[0]

        return full_text

    except Exception as e:
        print("AI Error:", e)
        return ""