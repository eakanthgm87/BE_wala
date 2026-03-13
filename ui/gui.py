import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import itertools
import time
import subprocess

from core.command_handler import handle_command


COMMAND_ICONS = {
    "git": "🔧",
    "pip": "📦",
    "python": "🐍",
    "npm": "📦",
    "docker": "🐳",
    "ls": "📁"
}

STATUS_ICONS = {
    "success": "✅",
    "error": "❌",
    "running": "⏳"
}


def ollama_translate(query):

    try:

        prompt = f"""
Convert the following request into a single Windows shell command.
Only return the command. Do not explain.

Request: {query}
Command:
"""

        result = subprocess.run(
            ["ollama", "run", "tinyllama"],
            input=prompt,
            text=True,
            capture_output=True
        )

        cmd = result.stdout.strip().split("\n")[0]

        return cmd

    except Exception:
        return query


def get_icon(cmd):
    for k in COMMAND_ICONS:
        if cmd.startswith(k):
            return COMMAND_ICONS[k]
    return "⚡"


class GradientFrame(tk.Canvas):

    def __init__(self, parent, c1, c2):
        super().__init__(parent, highlightthickness=0)
        self.c1 = c1
        self.c2 = c2
        self.bind("<Configure>", self.draw)

    def draw(self, event=None):

        self.delete("all")

        w = self.winfo_width()
        h = self.winfo_height()

        r1, g1, b1 = self.winfo_rgb(self.c1)
        r2, g2, b2 = self.winfo_rgb(self.c2)

        r_ratio = (r2 - r1) / h
        g_ratio = (g2 - g1) / h
        b_ratio = (b2 - b1) / h

        for i in range(h):

            nr = int(r1 + r_ratio * i)
            ng = int(g1 + g_ratio * i)
            nb = int(b1 + b_ratio * i)

            color = "#%4.4x%4.4x%4.4x" % (nr, ng, nb)

            self.create_line(0, i, w, i, fill=color)


def fade_in(widget, steps=10, delay=15):

    widget.update()

    for i in range(steps):
        widget.update()
        time.sleep(delay / 1000)


class CommandBlock:

    def __init__(self, parent, command, logs):

        self.start = time.time()
        self.logs = logs

        icon = get_icon(command)

        self.frame = tk.Frame(parent, bg="#1a1a1a", bd=1, relief="solid")

        header = tk.Frame(self.frame, bg="#222")
        header.pack(fill="x")

        self.status = tk.Label(header, text=STATUS_ICONS["running"], bg="#222")
        self.status.pack(side="left", padx=4)

        tk.Label(
            header,
            text=f"{icon} {command}",
            bg="#222",
            fg="#4cc9f0",
            font=("Consolas", 11, "bold")
        ).pack(side="left", padx=4)

        self.time = tk.Label(header, text="0s", bg="#222", fg="#aaa")
        self.time.pack(side="right", padx=6)

        self.toggle = tk.Button(
            header,
            text="▼",
            bg="#222",
            fg="white",
            relief="flat",
            command=self.toggle_view
        )
        self.toggle.pack(side="right")

        self.output = tk.Text(
            self.frame,
            height=6,
            bg="#0c0c0c",
            fg="white",
            font=("Consolas", 11),
            wrap="word"
        )

        self.output.pack(fill="x", padx=5, pady=5)

        self.collapsed = False

    def write_cmd(self, cmd):
        self.output.insert("end", cmd + "\n\n")

    def write_out(self, text):
        self.output.insert("end", text)
        self.logs.insert("end", text + "\n")

    def finish(self, success=True):

        duration = round(time.time() - self.start, 2)
        self.time.config(text=f"{duration}s")

        if success:
            self.status.config(text=STATUS_ICONS["success"])
        else:
            self.status.config(text=STATUS_ICONS["error"])

    def toggle_view(self):

        if self.collapsed:
            self.output.pack(fill="x", padx=5, pady=5)
            self.toggle.config(text="▼")
        else:
            self.output.pack_forget()
            self.toggle.config(text="▶")

        self.collapsed = not self.collapsed


def type_text(widget, text):

    for c in text:
        try:
            widget.insert("end", c)
            widget.see("end")
            widget.update()
            time.sleep(0.01)
        except:
            break


def launch_gui():

    root = tk.Tk()
    root.title("ShellMind AI Terminal")
    root.geometry("1300x750")

    gradient = GradientFrame(root, "#121212", "#1e1e1e")
    gradient.pack(fill="both", expand=True)

    history = []

    header = tk.Frame(gradient, bg="#1f1f1f")
    header.pack(fill="x")

    tk.Label(
        header,
        text="ShellMind AI Terminal",
        fg="#00ff9c",
        bg="#1f1f1f",
        font=("Consolas", 14, "bold")
    ).pack(side="left", padx=10)

    status = tk.Label(header, text="READY", bg="#1f1f1f", fg="#aaa")
    status.pack(side="right", padx=10)

    main = tk.Frame(gradient, bg="#121212")
    main.pack(fill="both", expand=True)

    canvas = tk.Canvas(main, bg="#121212", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    scroll = tk.Scrollbar(main, command=canvas.yview)
    scroll.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scroll.set)

    inner = tk.Frame(canvas, bg="#121212")
    canvas.create_window((0, 0), window=inner, anchor="nw")

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    sidebar = tk.Frame(main, width=320, bg="#1e1e1e")
    sidebar.pack(side="right", fill="y")

    tk.Label(sidebar, text="AI Assistant",
             fg="#00ff9c", bg="#1e1e1e",
             font=("Consolas", 12, "bold")).pack(pady=6)

    chat = scrolledtext.ScrolledText(sidebar, bg="#121212", fg="white", height=15)
    chat.pack(fill="x", padx=8)

    tk.Label(sidebar, text="Logs Viewer",
             fg="#ffaa00", bg="#1e1e1e",
             font=("Consolas", 11, "bold")).pack(pady=6)

    logs = scrolledtext.ScrolledText(sidebar, bg="#0c0c0c", fg="#aaa", height=15)
    logs.pack(fill="both", expand=True, padx=8)

    input_frame = tk.Frame(root, bg="#121212")
    input_frame.pack(fill="x")

    tk.Label(input_frame, text="shellmind >",
             fg="#00ff9c", bg="#121212",
             font=("Consolas", 12)).pack(side="left", padx=5)

    entry = tk.Entry(input_frame, bg="#1e1e1e", fg="white",
                     insertbackground="white",
                     font=("Consolas", 12))
    entry.pack(side="left", fill="x", expand=True, padx=5)

    def run(e):

        user = entry.get()
        if not user:
            return

        entry.delete(0, "end")
        history.append(user)

        block = CommandBlock(inner, user, logs)
        block.frame.pack(fill="x", padx=5, pady=5)

        fade_in(block.frame)

        threading.Thread(
            target=execute_cli,
            args=(block, user),
            daemon=True
        ).start()

    def execute_cli(block, user):

        spinner_cycle = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])

        running = True
        start_time = time.time()

        def spinner():
            if running:
                icon = next(spinner_cycle)
                root.after(0, lambda: block.status.config(text=f"{icon} Running..."))
                root.after(120, spinner)

        spinner()

        def stream(line):
            root.after(0, lambda: (
                block.output.insert("end", line),
                block.output.see("end")
            ))

        out = handle_command(user, stream_callback=stream)

        running = False

        duration = round(time.time() - start_time, 2)

        if "error" in out.lower() or "failed" in out.lower():
            icon = "❌"
        else:
            icon = "✅"

        root.after(0, lambda: block.status.config(text=f"{icon} Done ({duration}s)"))

    entry.bind("<Return>", run)

    root.mainloop()