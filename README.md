# 🤖 AI Command Terminal

An **AI-powered developer terminal** that converts **natural language instructions into safe executable system commands**.

Instead of remembering complex terminal commands, you can simply type:

```
ai: find all python files
ai: delete temporary files
ai: explain docker
```

The AI understands your intent, generates the correct command, checks for safety, and executes it.

---

# 🎥 Demo Video

Click the thumbnail below to watch the demo.

  https://youtu.be/g6Zi8TGvVqk

---

# 🚀 Features

## 🧠 Natural Language Commands

Write commands in **plain English** and the AI converts them into terminal commands.

Example:

User Input

```
ai: list all python files
```

Generated Command

```
find . -name "*.py"
```

---

## 🛡 AI Safety Guard

The system automatically blocks **dangerous commands** like:

```
rm -rf /
shutdown
format disk
```

Risky commands require confirmation before execution.

---

## 👁 Command Preview System

Before running a command, the system displays:

• Generated command
• Risk level
• Execution confirmation

This prevents accidental destructive commands.

---

## 💬 AI Chat Mode

If the input is a **question instead of a command**, the system switches to **chat mode**.

Example:

```
ai: what is docker
ai: explain git branching
```

---

## ⚡ Self-Healing Terminal

If a command fails, the AI can:

1. Analyze the error
2. Suggest corrections
3. Retry with a fixed command

---

# 🏗 Project Structure

```
AI Command Terminal
│
├── ai/
│   ├── ai_engine.py
│   ├── natural_commands.py
│   ├── ollama_client.py
│   └── prompts.py
│
├── safety/
│   └── command_guard.py
│
├── core/
│   └── terminal_executor.py
│
├── .snapshots/
│
├── main.py
└── README.md
```

---

# ⚙ Installation

## 1 Clone the repository

```
git clone https://github.com/eakanthgm87/BE_wala.git
```

```
cd BE_wala
```

---

## 2 Install dependencies

```
pip install -r requirements.txt
```

---

## 3 Install AI Model

This project uses **Ollama** to run local AI models.

Install Ollama from:

https://ollama.ai

Run a model:

```
ollama run llama3
```

---

# ▶ Running the Project

Start the AI terminal:

```
python main.py
```

Example usage:

```
ai: show running processes
ai: delete temp files
ai: explain kubernetes
```

---

# 💡 Example Workflow

User Input

```
ai: find all python files
```

AI Generated Command

```
find . -name "*.py"
```

Output

```
./src/app.py
./tests/test_api.py
```

---

# 🔒 Security Features

• Dangerous command detection
• Risk scoring
• Command confirmation
• Execution safety checks

---

# 🧩 Future Improvements

• Voice-controlled terminal
• Multi-model AI support
• Git integration
• Auto debugging system
• Cloud deployment

---

# 📜 License

MIT License

---

# ⭐ Support

If you like this project, consider **starring the repository on GitHub**.
