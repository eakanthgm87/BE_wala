"""
dockerfile_generator.py
------------------------
Fully self-contained. No imports from ai_deploy_runner.
Works with both the old and new version of the deployment module.
"""

from pathlib import Path
import os
import re


# ── Entry-point candidates per framework ──────────────────────────────────────

_ENTRY = {
    "fastapi":   ["main.py", "app.py", "server.py", "api.py"],
    "flask":     ["app.py", "run.py", "main.py", "wsgi.py"],
    "django":    ["manage.py"],
    "streamlit": ["app.py", "main.py", "streamlit_app.py"],
    "python":    ["main.py", "app.py", "run.py", "server.py", "index.py"],
    "nodejs":    ["index.js", "server.js", "app.js", "main.js"],
}

_PORT = {
    "fastapi": 8000, "flask": 5000, "django": 8000,
    "streamlit": 8501, "react": 80, "nextjs": 3000,
    "nodejs": 3000, "python": 8000,
    "go": 8080, "rust": 8080, "java-maven": 8080,
    "java-gradle": 8080, "dotnet": 8080, "ruby": 3000,
    "rails": 3000, "php": 80, "static": 80,
}


def _find_entry(path: Path, framework: str) -> str:
    candidates = _ENTRY.get(framework, ["main.py", "app.py"])
    for c in candidates:
        if (path / c).exists():
            return c
    py = sorted(path.glob("*.py"))
    if py:
        return py[0].name
    return "main.py"


def _detect_java_version(path: Path) -> int:
    for fname in ["build.gradle", "build.gradle.kts", "pom.xml"]:
        f = path / fname
        if not f.exists():
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"JavaLanguageVersion\.of\((\d+)\)", txt)
            if m:
                return int(m.group(1))
            m = re.search(r"sourceCompatibility\s*=\s*['\"]?(\d+)['\"]?", txt)
            if m:
                return int(m.group(1))
            m = re.search(r"VERSION_(\d+)", txt)
            if m:
                return int(m.group(1))
            m = re.search(r"<java\.version>(\d+)</java\.version>", txt)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    return 17


def _make_dockerfile(framework: str, entry: str, port: int, path: Path) -> str:
    """Return Dockerfile content as a plain ASCII string."""

    fw = framework.lower()

    # ── Python frameworks ─────────────────────────────────────────────────────
    if fw in ("fastapi", "uvicorn"):
        module = entry.replace(".py", "")
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt* ./\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["uvicorn", "{mod}:app", "--host", "0.0.0.0", "--port", "{port}"]\n'
        ).format(port=port, mod=module)

    if fw == "flask":
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt* ./\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["python", "{entry}"]\n'
        ).format(port=port, entry=entry)

    if fw == "django":
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt* ./\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["python", "manage.py", "runserver", "0.0.0.0:{port}"]\n'
        ).format(port=port)

    if fw == "streamlit":
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt* ./\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["streamlit", "run", "{entry}", '
            '"--server.port={port}", "--server.address=0.0.0.0"]\n'
        ).format(port=port, entry=entry)

    if fw == "python":
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY requirements.txt* ./\n"
            "RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["python", "{entry}"]\n'
        ).format(port=port, entry=entry)

    # ── Node.js frameworks ────────────────────────────────────────────────────
    if fw == "react":
        return (
            "FROM node:20-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm ci\n"
            "COPY . .\n"
            "RUN npm run build\n\n"
            "FROM nginx:alpine\n"
            "COPY --from=builder /app/build /usr/share/nginx/html\n"
            "EXPOSE 80\n"
            'CMD ["nginx", "-g", "daemon off;"]\n'
        )

    if fw == "nextjs":
        return (
            "FROM node:20-alpine\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm ci\n"
            "COPY . .\n"
            "RUN npm run build\n"
            "EXPOSE {port}\n"
            'CMD ["npm", "start"]\n'
        ).format(port=port)

    if fw in ("nodejs", "node", "express"):
        return (
            "FROM node:20-alpine\n"
            "WORKDIR /app\n"
            "COPY package*.json ./\n"
            "RUN npm ci --omit=dev\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["node", "{entry}"]\n'
        ).format(port=port, entry=entry)

    # ── Go ────────────────────────────────────────────────────────────────────
    if fw == "go":
        return (
            "FROM golang:1.22-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY go.mod go.sum* ./\n"
            "RUN go mod download\n"
            "COPY . .\n"
            "RUN go build -o /app/server .\n\n"
            "FROM alpine:3.19\n"
            "WORKDIR /app\n"
            "COPY --from=builder /app/server /app/server\n"
            "EXPOSE {port}\n"
            'CMD ["/app/server"]\n'
        ).format(port=port)

    # ── Rust ──────────────────────────────────────────────────────────────────
    if fw == "rust":
        return (
            "FROM rust:1.77-slim AS builder\n"
            "WORKDIR /app\n"
            "COPY Cargo.toml Cargo.lock* ./\n"
            "RUN mkdir src && echo 'fn main(){}' > src/main.rs "
            "&& cargo build --release && rm -rf src\n"
            "COPY . .\n"
            "RUN cargo build --release\n\n"
            "FROM debian:bookworm-slim\n"
            "WORKDIR /app\n"
            "COPY --from=builder /app/target/release/app /app/server\n"
            "EXPOSE {port}\n"
            'CMD ["/app/server"]\n'
        ).format(port=port)

    # ── Java Gradle ───────────────────────────────────────────────────────────
    if fw == "java-gradle":
        jv = _detect_java_version(path)
        return (
            "FROM gradle:8-jdk{jv} AS builder\n"
            "WORKDIR /app\n"
            "COPY build.gradle* settings.gradle* gradlew* ./\n"
            "COPY gradle gradle/\n"
            "RUN ./gradlew dependencies --no-daemon -q 2>/dev/null || true\n"
            "COPY . .\n"
            "RUN ./gradlew bootJar --no-daemon -q "
            "-Porg.gradle.java.installations.auto-detect=false "
            "-Porg.gradle.java.installations.auto-download=false "
            "2>/dev/null || "
            "./gradlew jar --no-daemon -q "
            "-Porg.gradle.java.installations.auto-detect=false "
            "-Porg.gradle.java.installations.auto-download=false\n\n"
            "FROM eclipse-temurin:{jv}-jre-alpine\n"
            "WORKDIR /app\n"
            "COPY --from=builder /app/build/libs/*.jar /app/app.jar\n"
            "EXPOSE {port}\n"
            'CMD ["java", "-jar", "/app/app.jar"]\n'
        ).format(jv=jv, port=port)

    # ── Java Maven ────────────────────────────────────────────────────────────
    if fw == "java-maven":
        jv = _detect_java_version(path)
        return (
            "FROM maven:3.9-eclipse-temurin-{jv} AS builder\n"
            "WORKDIR /app\n"
            "COPY pom.xml ./\n"
            "RUN mvn dependency:go-offline -q\n"
            "COPY . .\n"
            "RUN mvn package -DskipTests -q\n\n"
            "FROM eclipse-temurin:{jv}-jre-alpine\n"
            "WORKDIR /app\n"
            "COPY --from=builder /app/target/*.jar /app/app.jar\n"
            "EXPOSE {port}\n"
            'CMD ["java", "-jar", "/app/app.jar"]\n'
        ).format(jv=jv, port=port)

    # ── Ruby / Rails ──────────────────────────────────────────────────────────
    if fw == "rails":
        return (
            "FROM ruby:3.3-slim\n"
            "WORKDIR /app\n"
            "COPY Gemfile Gemfile.lock* ./\n"
            "RUN bundle install --without development test\n"
            "COPY . .\n"
            "RUN bundle exec rake assets:precompile 2>/dev/null || true\n"
            "EXPOSE {port}\n"
            'CMD ["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]\n'
        ).format(port=port)

    if fw == "ruby":
        return (
            "FROM ruby:3.3-slim\n"
            "WORKDIR /app\n"
            "COPY Gemfile Gemfile.lock* ./\n"
            "RUN bundle install --without development test\n"
            "COPY . .\n"
            "EXPOSE {port}\n"
            'CMD ["ruby", "{entry}"]\n'
        ).format(port=port, entry=entry)

    # ── PHP ───────────────────────────────────────────────────────────────────
    if fw == "php":
        return (
            "FROM php:8.3-apache\n"
            "WORKDIR /var/www/html\n"
            "COPY . .\n"
            "EXPOSE 80\n"
            'CMD ["apache2-foreground"]\n'
        )

    # ── .NET ──────────────────────────────────────────────────────────────────
    if fw == "dotnet":
        return (
            "FROM mcr.microsoft.com/dotnet/sdk:8.0 AS builder\n"
            "WORKDIR /app\n"
            "COPY *.csproj ./\n"
            "RUN dotnet restore\n"
            "COPY . .\n"
            "RUN dotnet publish -c Release -o /app/publish\n\n"
            "FROM mcr.microsoft.com/dotnet/aspnet:8.0\n"
            "WORKDIR /app\n"
            "COPY --from=builder /app/publish .\n"
            "EXPOSE {port}\n"
            'CMD ["dotnet", "app.dll"]\n'
        ).format(port=port)

    # ── Static HTML ───────────────────────────────────────────────────────────
    if fw == "static":
        return (
            "FROM nginx:alpine\n"
            "COPY . /usr/share/nginx/html\n"
            "EXPOSE 80\n"
            'CMD ["nginx", "-g", "daemon off;"]\n'
        )

    # ── Default fallback: generic Python ─────────────────────────────────────
    return (
        "FROM python:3.11-slim\n"
        "WORKDIR /app\n"
        "COPY requirements.txt* ./\n"
        "RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true\n"
        "COPY . .\n"
        "EXPOSE {port}\n"
        'CMD ["python", "{entry}"]\n'
    ).format(port=port, entry=entry)


# ── Framework detection (self-contained, no external imports) ─────────────────

def _detect_framework(path: Path) -> str:
    try:
        files = {f.name.lower() for f in path.iterdir() if f.is_file()}
    except Exception:
        return "python"

    if any(f.endswith(".csproj") or f.endswith(".fsproj") for f in files):
        return "dotnet"
    if "pom.xml" in files:
        return "java-maven"
    if "build.gradle" in files or "build.gradle.kts" in files:
        return "java-gradle"
    if "go.mod" in files:
        return "go"
    if "cargo.toml" in files:
        return "rust"
    if "gemfile" in files:
        try:
            txt = (path / "Gemfile").read_text(encoding="utf-8", errors="ignore").lower()
            return "rails" if "rails" in txt else "ruby"
        except Exception:
            return "ruby"
    if "composer.json" in files or any(f.endswith(".php") for f in files):
        return "php"
    if "package.json" in files:
        try:
            import json
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                return "nextjs"
            if "react" in deps or "react-dom" in deps:
                return "react"
        except Exception:
            pass
        return "nodejs"
    reqs = ""
    if "requirements.txt" in files:
        try:
            reqs = (path / "requirements.txt").read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            pass
    if "pyproject.toml" in files:
        try:
            reqs += (path / "pyproject.toml").read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            pass
    if reqs or "setup.py" in files:
        for kw, fw in [("fastapi","fastapi"),("uvicorn","fastapi"),
                       ("django","django"),("streamlit","streamlit"),("flask","flask")]:
            if kw in reqs:
                return fw
        return "python"
    if any(f.endswith(".py") for f in files):
        return "python"
    if "index.html" in files or any(f.endswith(".html") for f in files):
        return "static"
    return "python"


# ── Public class ──────────────────────────────────────────────────────────────

class DockerfileGenerator:
    """Generates Dockerfiles. Fully self-contained — no ai_deploy_runner needed."""

    def generate_dockerfile(self, project_info: dict, output_path: str = ".") -> str:
        """Detect language, generate Dockerfile, write to disk, return path."""
        path = Path(output_path).resolve()

        # Use framework from project_info if provided, otherwise auto-detect
        framework = project_info.get("framework", "").lower()
        if not framework or framework == "unknown":
            framework = _detect_framework(path)

        port  = _PORT.get(framework, 8000)
        entry = _find_entry(path, framework)

        # Override port from project_info if available
        ports = project_info.get("ports", [])
        if ports:
            port = ports[0]

        content = _make_dockerfile(framework, entry, port, path)

        df = path / "Dockerfile"
        df.write_text(content, encoding="utf-8")
        print("   [Dockerfile] {}  port={}  entry={}".format(framework, port, entry))
        return str(df)

    def generate_optimized_dockerfile(self, service_config: dict,
                                       project_path: str = ".") -> str:
        """Return Dockerfile content as string (does not write to disk)."""
        fw    = service_config.get("framework", "python").lower()
        port  = service_config.get("port") or _PORT.get(fw, 8000)
        path  = Path(project_path)
        entry = _find_entry(path, fw)
        return _make_dockerfile(fw, entry, port, path)

    # ── Legacy shims ──────────────────────────────────────────────────────────

    def select_template(self, service_config: dict) -> dict:
        fw = service_config.get("framework", "python").lower()
        images = {
            "fastapi":     ("python:3.11-slim",  "python:3.11-slim"),
            "flask":       ("python:3.11-slim",  "python:3.11-slim"),
            "django":      ("python:3.11-slim",  "python:3.11-slim"),
            "streamlit":   ("python:3.11-slim",  "python:3.11-slim"),
            "python":      ("python:3.11-slim",  "python:3.11-slim"),
            "react":       ("node:20-alpine",    "nginx:alpine"),
            "nextjs":      ("node:20-alpine",    "node:20-alpine"),
            "nodejs":      ("node:20-alpine",    "node:20-alpine"),
            "go":          ("golang:1.22-alpine","alpine:3.19"),
            "java-gradle": ("gradle:8-jdk17",    "eclipse-temurin:17-jre-alpine"),
            "java-maven":  ("maven:3.9-eclipse-temurin-17", "eclipse-temurin:17-jre-alpine"),
        }
        base, runtime = images.get(fw, ("python:3.11-slim", "python:3.11-slim"))
        return {"base_image": base, "runtime_image": runtime,
                "install_cmd": "", "run_cmd": ""}

    def copy_dependency_files(self, service_config: dict) -> str:
        fw = service_config.get("framework", "python").lower()
        if fw in ("react", "nextjs", "nodejs"):
            return "COPY package*.json ./"
        return "COPY requirements.txt* ./"

    def get_install_command(self, service_config: dict) -> str:
        fw = service_config.get("framework", "python").lower()
        if fw in ("react", "nextjs", "nodejs"):
            return "npm ci"
        return "pip install --no-cache-dir -r requirements.txt"

    def get_build_command(self, service_config: dict) -> str:
        fw = service_config.get("framework", "python").lower()
        if fw in ("react", "nextjs"):
            return "RUN npm run build"
        return ""

    def get_run_command(self, service_config: dict) -> str:
        fw    = service_config.get("framework", "python").lower()
        port  = service_config.get("port", 8000)
        entry = service_config.get("entry_point", "main.py")
        if fw == "fastapi":
            return 'CMD ["uvicorn", "{}:app", "--host", "0.0.0.0", "--port", "{}"]'.format(
                entry.replace(".py", ""), port)
        if fw in ("nodejs", "react", "nextjs"):
            return 'CMD ["node", "{}"]'.format(entry)
        return 'CMD ["python", "{}"]'.format(entry)

    def get_optimizations(self, _service_config: dict) -> list:
        return []

    def _simple_python_dockerfile(self, script_name: str) -> str:
        return (
            "FROM python:3.11-slim\n"
            "WORKDIR /app\n"
            "COPY . .\n"
            "RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true\n"
            'CMD ["python", "{}"]\n'.format(script_name)
        )

    def _fastapi_dockerfile(self):
        return self.generate_optimized_dockerfile({"framework": "fastapi", "port": 8000})

    def _flask_dockerfile(self):
        return self.generate_optimized_dockerfile({"framework": "flask", "port": 5000})

    def _django_dockerfile(self):
        return self.generate_optimized_dockerfile({"framework": "django", "port": 8000})

    def _nodejs_dockerfile(self):
        return self.generate_optimized_dockerfile({"framework": "nodejs", "port": 3000})

    def _get_dockerfile_content(self, framework: str, _info: dict) -> str:
        return self.generate_optimized_dockerfile({"framework": framework.lower(), "port": 8000})
