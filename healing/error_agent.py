"""
error_agent.py

ShellMind Error Agent — scans project folders for code errors and fixes them using AI.

Commands supported:
    ai: scan project
    ai: fix errors
    ai: fix file <path>
    ai: clear errors
    ai: show errors
    ai: explain errors
"""

import os
import ast
import json
import subprocess

from pathlib import Path

from ai.ai_engine import ask_ai


# ═══════════════════════════════════════════════════════════════════════════════
# FILE TYPES TO SCAN
# ═══════════════════════════════════════════════════════════════════════════════

SCANNABLE_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "react",
    ".tsx": "react-typescript",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c-header",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".dart": "dart",
    ".m": "objective-c",
    ".mm": "objective-c++",

    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",

    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "config",
    ".env": "env",

    ".sh": "shell",
    ".bash": "bash",
    ".zsh": "zsh",
    ".bat": "batch",
    ".ps1": "powershell",

    ".sql": "sql",
    ".csv": "csv",
    ".tsv": "tsv",

    ".dockerfile": "docker",
    ".tf": "terraform",

    ".gradle": "gradle",
    ".xml": "xml",
    ".plist": "ios-config",

    ".md": "markdown",
    ".txt": "text"
}

SKIP_DIRS = {
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".git",
    "dist",
    "build",
}


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR DETECTOR
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorDetector:

    # ---------------------------
    # PYTHON
    # ---------------------------

    def check_python_syntax(self, filepath):

        errors = []

        try:
            source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
            ast.parse(source)

        except SyntaxError as e:

            errors.append({
                "file": filepath,
                "line": e.lineno or 0,
                "type": "PythonSyntaxError",
                "message": e.msg,
                "text": e.text.strip() if e.text else ""
            })

        return errors


    # ---------------------------
    # JSON
    # ---------------------------

    def check_json(self, filepath):

        errors = []

        try:
            source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
            json.loads(source)

        except json.JSONDecodeError as e:

            errors.append({
                "file": filepath,
                "line": e.lineno,
                "type": "JSONError",
                "message": e.msg,
                "text": ""
            })

        return errors


    # ---------------------------
    # JAVA
    # ---------------------------

    def check_java(self, filepath):

        result = subprocess.run(
            ["javac", filepath],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            return [{
                "file": filepath,
                "line": 0,
                "type": "JavaCompileError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # JAVASCRIPT / TYPESCRIPT
    # ---------------------------

    def check_js(self, filepath):

        result = subprocess.run(
            ["node", "--check", filepath],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            return [{
                "file": filepath,
                "line": 0,
                "type": "JavaScriptSyntaxError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # C / C++
    # ---------------------------

    def check_c_cpp(self, filepath):

        compiler = "gcc"

        if filepath.endswith(".cpp"):
            compiler = "g++"

        result = subprocess.run(
            [compiler, "-fsyntax-only", filepath],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:

            return [{
                "file": filepath,
                "line": 0,
                "type": "CompileError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # GO
    # ---------------------------

    def check_go(self, filepath):

        result = subprocess.run(
            ["go", "vet", filepath],
            capture_output=True,
            text=True
        )

        if result.stderr:

            return [{
                "file": filepath,
                "line": 0,
                "type": "GoError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # RUST
    # ---------------------------

    def check_rust(self, filepath):

        result = subprocess.run(
            ["rustc", "--emit", "metadata", filepath],
            capture_output=True,
            text=True
        )

        if result.stderr:

            return [{
                "file": filepath,
                "line": 0,
                "type": "RustCompileError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # PHP
    # ---------------------------

    def check_php(self, filepath):

        result = subprocess.run(
            ["php", "-l", filepath],
            capture_output=True,
            text=True
        )

        if "Errors parsing" in result.stdout:

            return [{
                "file": filepath,
                "line": 0,
                "type": "PHPSyntaxError",
                "message": result.stdout.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # RUBY
    # ---------------------------

    def check_ruby(self, filepath):

        result = subprocess.run(
            ["ruby", "-c", filepath],
            capture_output=True,
            text=True
        )

        if "Syntax OK" not in result.stdout:

            return [{
                "file": filepath,
                "line": 0,
                "type": "RubySyntaxError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # SHELL
    # ---------------------------

    def check_shell(self, filepath):

        result = subprocess.run(
            ["bash", "-n", filepath],
            capture_output=True,
            text=True
        )

        if result.stderr:

            return [{
                "file": filepath,
                "line": 0,
                "type": "ShellSyntaxError",
                "message": result.stderr.strip(),
                "text": ""
            }]

        return []


    # ---------------------------
    # ROUTER
    # ---------------------------

    def check_file(self, filepath):

        ext = Path(filepath).suffix.lower()

        if ext == ".py":
            return self.check_python_syntax(filepath)

        if ext == ".json":
            return self.check_json(filepath)

        if ext == ".java":
            return self.check_java(filepath)

        if ext in [".js", ".ts"]:
            return self.check_js(filepath)

        if ext in [".c", ".cpp"]:
            return self.check_c_cpp(filepath)

        if ext == ".go":
            return self.check_go(filepath)

        if ext == ".rs":
            return self.check_rust(filepath)

        if ext == ".php":
            return self.check_php(filepath)

        if ext == ".rb":
            return self.check_ruby(filepath)

        if ext in [".sh", ".bash"]:
            return self.check_shell(filepath)

        return []


    def scan_folder(self, folder="."):

        results = {}

        root = Path(folder).resolve()

        for dirpath, dirnames, filenames in os.walk(root):

            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

            for filename in filenames:

                ext = Path(filename).suffix.lower()

                if ext not in SCANNABLE_EXTENSIONS:
                    continue

                filepath = str(Path(dirpath) / filename)

                errors = self.check_file(filepath)

                if errors:
                    results[filepath] = errors

        return results


# ═══════════════════════════════════════════════════════════════════════════════
# AI FIXER
# ═══════════════════════════════════════════════════════════════════════════════


class AIFixer:

    def build_prompt(self, source, errors):

        error_text = "\n".join(
            f"Line {e['line']}: {e['message']}" for e in errors
        )

        prompt = f"""
Fix the following code errors.

Errors:
{error_text}

Code:
{source}

Return ONLY corrected code.
"""

        return prompt


    def fix_code(self, source, errors):

        prompt = self.build_prompt(source, errors)

        fixed = ask_ai(prompt, "code fixing", "auto")

        if not fixed:
            return None

        if fixed.startswith("```"):
            lines = fixed.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            fixed = "\n".join(lines)

        return fixed.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR AGENT
# ═══════════════════════════════════════════════════════════════════════════════


class ErrorAgent:

    def __init__(self):

        self.detector = ErrorDetector()
        self.fixer = AIFixer()
        self.last_scan = {}


    # ───────────────────────────────────────────
    # SCAN PROJECT
    # ───────────────────────────────────────────

    def cmd_scan(self, cwd="."):

        print("[ShellMind] Scanning project...")

        results = self.detector.scan_folder(cwd)

        self.last_scan = results

        if not results:
            return "[ShellMind] No errors found."

        lines = []
        total = 0

        for filepath, errors in results.items():

            rel = os.path.relpath(filepath, cwd)

            lines.append(f"\n{rel}")

            for e in errors:

                lines.append(
                    f"  Line {e['line']} [{e['type']}]: {e['message']}"
                )

                if e["text"]:
                    lines.append(f"    → {e['text']}")

                total += 1

        lines.append(f"\nTotal errors: {total}")

        return "\n".join(lines)


    # ───────────────────────────────────────────
    # SHOW ERRORS
    # ───────────────────────────────────────────

    def cmd_show_errors(self, cwd="."):

        if not self.last_scan:
            return self.cmd_scan(cwd)

        return self.cmd_scan(cwd)


    # ───────────────────────────────────────────
    # EXPLAIN ERRORS
    # ───────────────────────────────────────────

    def cmd_explain_errors(self):

        if not self.last_scan:
            return "Run 'ai: scan project' first."

        lines = []

        for filepath, errors in self.last_scan.items():

            for e in errors:

                explanation = self._explain(e)

                lines.append(
                    f"{filepath} line {e['line']} → {explanation}"
                )

        return "\n".join(lines)


    def _explain(self, error):

        msg = error["message"].lower()

        if "invalid syntax" in msg:
            return "Python syntax error. Likely missing colon, bracket, or quote."

        if "unexpected eof" in msg:
            return "File ended unexpectedly. Missing closing bracket."

        if "indent" in msg:
            return "Indentation problem."

        return error["message"]


    # ───────────────────────────────────────────
    # FIX FILE
    # ───────────────────────────────────────────

    def cmd_fix_file(self, filepath, cwd="."):

        full_path = os.path.join(cwd, filepath)

        if not os.path.exists(full_path):
            return f"File not found: {filepath}"

        errors = self.detector.check_file(full_path)

        if not errors:
            return "No errors found."

        print(f"[ShellMind] Fixing {filepath} with AI...")

        source = Path(full_path).read_text(encoding="utf-8", errors="ignore")

        fixed = self.fixer.fix_code(source, errors)

        if not fixed:
            return "AI could not fix the file."

        # Safety check 1: avoid empty responses
        if len(fixed.strip()) < 5:
            return "AI returned incomplete code. Fix aborted."

        # Safety check 2: avoid identical response (AI didn't change anything)
        if fixed.strip() == source.strip():
            return "AI returned same code. No changes applied."

        backup = full_path + ".bak"

        Path(backup).write_text(source, encoding="utf-8")

        Path(full_path).write_text(fixed, encoding="utf-8")

        return f"File fixed. Backup saved as {backup}"


    # ───────────────────────────────────────────
    # FIX ALL FILES
    # ───────────────────────────────────────────

    def cmd_fix_all(self, cwd="."):

        results = self.detector.scan_folder(cwd)

        if not results:
            return "No errors found."

        lines = []

        for filepath in results:

            rel = os.path.relpath(filepath, cwd)

            lines.append(self.cmd_fix_file(rel, cwd))

        return "\n".join(lines)


    # ───────────────────────────────────────────
    # CLEAR ERRORS
    # ───────────────────────────────────────────

    def cmd_clear_errors(self, cwd="."):

        results = self.detector.scan_folder(cwd)

        if not results:
            return "No errors found."

        lines = []

        for filepath, errors in results.items():

            ext = Path(filepath).suffix

            if ext not in [".py", ".java", ".js", ".c", ".cpp"]:
                continue

            source = Path(filepath).read_text(encoding="utf-8", errors="ignore").splitlines()

            error_lines = {e["line"] for e in errors}

            new_code = []

            for i, line in enumerate(source, start=1):

                if i in error_lines:

                    # choose correct comment style
                    if ext == ".py":
                        new_code.append(f"# CLEARED ERROR → {line}")

                    elif ext in [".java", ".js", ".c", ".cpp"]:
                        new_code.append(f"// CLEARED ERROR → {line}")

                    else:
                        new_code.append(f"# CLEARED ERROR → {line}")

                else:
                    new_code.append(line)

            backup = filepath + ".bak"

            Path(backup).write_text("\n".join(source), encoding="utf-8")

            Path(filepath).write_text("\n".join(new_code), encoding="utf-8")

            lines.append(f"Cleared errors in {filepath}")

        return "\n".join(lines)


# Singleton instance
error_agent = ErrorAgent()