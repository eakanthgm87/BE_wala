# -*- coding: utf-8 -*-
"""
ai_deploy_runner.py
-------------------------------------------------------------------
Language-independent one-click deploy engine.

Auto-detects and supports:
  Python  -> FastAPI, Flask, Django, Streamlit, generic
  Node.js -> React, Next.js, Express, generic Node
  Go      -> go.mod
  Rust    -> Cargo.toml
  Java    -> Maven (pom.xml) / Gradle (build.gradle)
  Ruby    -> Gemfile / Rails
  PHP     -> composer.json
  .NET    -> *.csproj / *.fsproj
  Static  -> HTML/CSS/JS only

Targets:
  run_deploy_docker(path, image, registry)
  run_deploy_k8s(path, image, registry)
  run_destroy(path, image, target)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ------------------------------------------------------------------
# Colours  (ASCII-only fallbacks so Windows cp1252 never crashes)
# ------------------------------------------------------------------

_TTY = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    _m = {
        "bold": "1", "green": "92", "yellow": "93",
        "red": "91", "cyan": "96", "dim": "2", "blue": "94",
    }
    return "\033[{}m{}\033[0m".format(_m[code], text) if _TTY else text

def _banner(title: str) -> None:
    w = 64
    bar = "+" + "=" * w + "+"
    pad = (w - len(title)) // 2
    middle = "|" + " " * pad + title + " " * (w - pad - len(title)) + "|"
    print("\n" + _c("bold", bar))
    print(_c("bold", "|") + " " * pad + _c("cyan", _c("bold", title))
          + " " * (w - pad - len(title)) + _c("bold", "|"))
    print(_c("bold", bar))

def _step(n: int, tot: int, msg: str) -> None:
    print("\n  {}  {}".format(_c("bold", _c("cyan", "[{}/{}]".format(n, tot))), msg))

def _ok(m: str)   -> None: print("        {}  {}".format(_c("green",  "[OK]  "), m))
def _warn(m: str) -> None: print("        {}  {}".format(_c("yellow", "[WARN]"), m))
def _fail(m: str) -> None: print("        {}  {}".format(_c("red",    "[FAIL]"), m), file=sys.stderr)
def _info(m: str) -> None: print("        {}  {}".format(_c("dim",    "->    "), m))


# ------------------------------------------------------------------
# Language / framework profiles
# ------------------------------------------------------------------
# Required keys: port, base_image, dep_copy, install, cmd
# Optional:      build, runtime_image, runtime_copy,
#                health_path, entry_detect
# {entry} and {entry_module} in cmd are replaced at runtime.
# ------------------------------------------------------------------

PROFILES: dict = {
    # Python
    "fastapi": {
        "port": 8000, "base_image": "python:3.11-slim",
        "dep_copy": "COPY requirements.txt* ./",
        "install": "RUN pip install --no-cache-dir -r requirements.txt",
        "cmd": '["uvicorn", "{entry_module}:app", "--host", "0.0.0.0", "--port", "8000"]',
        "entry_detect": ["main.py", "app.py", "server.py", "api.py", "asgi.py"],
        "health_path": "/health",
    },
    "flask": {
        "port": 5000, "base_image": "python:3.11-slim",
        "dep_copy": "COPY requirements.txt* ./",
        "install": "RUN pip install --no-cache-dir -r requirements.txt",
        "cmd": '["python", "{entry}"]',
        "entry_detect": ["app.py", "run.py", "main.py", "wsgi.py", "server.py"],
        "health_path": "/",
    },
    "django": {
        "port": 8000, "base_image": "python:3.11-slim",
        "dep_copy": "COPY requirements.txt* ./",
        "install": "RUN pip install --no-cache-dir -r requirements.txt",
        "cmd": '["python", "manage.py", "runserver", "0.0.0.0:8000"]',
        "health_path": "/",
    },
    "streamlit": {
        "port": 8501, "base_image": "python:3.11-slim",
        "dep_copy": "COPY requirements.txt* ./",
        "install": "RUN pip install --no-cache-dir -r requirements.txt",
        "cmd": '["streamlit", "run", "{entry}", "--server.port=8501", "--server.address=0.0.0.0"]',
        "entry_detect": ["app.py", "main.py", "streamlit_app.py"],
        "health_path": "/_stcore/health",
    },
    "python": {
        "port": 8000, "base_image": "python:3.11-slim",
        "dep_copy": "COPY requirements.txt* ./",
        "install": "RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true",
        "cmd": '["python", "{entry}"]',
        "entry_detect": ["main.py", "app.py", "run.py", "server.py", "index.py", "start.py"],
        "health_path": "/",
    },
    # Node.js
    "nextjs": {
        "port": 3000, "base_image": "node:20-alpine",
        "dep_copy": "COPY package*.json ./",
        "install": "RUN npm ci",
        "build": "RUN npm run build",
        "cmd": '["npm", "start"]',
        "health_path": "/",
    },
    "react": {
        "port": 80, "base_image": "node:20-alpine",
        "dep_copy": "COPY package*.json ./",
        "install": "RUN npm ci",
        "build": "RUN npm run build",
        "runtime_image": "nginx:alpine",
        "runtime_copy": "COPY --from=builder /app/build /usr/share/nginx/html",
        "cmd": '["nginx", "-g", "daemon off;"]',
        "health_path": "/",
    },
    "nodejs": {
        "port": 3000, "base_image": "node:20-alpine",
        "dep_copy": "COPY package*.json ./",
        "install": "RUN npm ci --omit=dev",
        "cmd": '["node", "{entry}"]',
        "entry_detect": ["index.js", "server.js", "app.js", "main.js", "src/index.js"],
        "health_path": "/",
    },
    # Go
    "go": {
        "port": 8080, "base_image": "golang:1.22-alpine",
        "dep_copy": "COPY go.mod go.sum* ./",
        "install": "RUN go mod download",
        "build": "RUN go build -o /app/server .",
        "runtime_image": "alpine:3.19",
        "runtime_copy": "COPY --from=builder /app/server /app/server",
        "cmd": '["/app/server"]',
        "health_path": "/health",
    },
    # Rust
    "rust": {
        "port": 8080, "base_image": "rust:1.77-slim",
        "dep_copy": "COPY Cargo.toml Cargo.lock* ./",
        "install": (
            "RUN mkdir src && echo 'fn main(){}' > src/main.rs "
            "&& cargo build --release && rm -rf src"
        ),
        "build": "RUN cargo build --release",
        "runtime_image": "debian:bookworm-slim",
        "runtime_copy": "COPY --from=builder /app/target/release/app /app/server",
        "cmd": '["/app/server"]',
        "health_path": "/health",
    },
    # Java Maven
    "java-maven": {
        "port": 8080, "base_image": "maven:3.9-eclipse-temurin-21",
        "dep_copy": "COPY pom.xml ./",
        "install": "RUN mvn dependency:go-offline -q",
        "build": "RUN mvn package -DskipTests -q",
        "runtime_image": "eclipse-temurin:21-jre-alpine",
        "runtime_copy": "COPY --from=builder /app/target/*.jar /app/app.jar",
        "cmd": '["java", "-jar", "/app/app.jar"]',
        "health_path": "/actuator/health",
    },
    # Java Gradle
    "java-gradle": {
        "port": 8080, "base_image": "gradle:8-jdk17",
        "dep_copy": "COPY build.gradle* settings.gradle* gradlew* ./\nCOPY gradle gradle/",
        "install": "RUN ./gradlew dependencies --no-daemon -q 2>/dev/null || true",
        "build": (
            "RUN ./gradlew bootJar --no-daemon -q "
            "-Porg.gradle.java.installations.auto-detect=false "
            "-Porg.gradle.java.installations.auto-download=false "
            "2>/dev/null || ./gradlew jar --no-daemon -q "
            "-Porg.gradle.java.installations.auto-detect=false "
            "-Porg.gradle.java.installations.auto-download=false"
        ),
        "runtime_image": "eclipse-temurin:17-jre-alpine",
        "runtime_copy": "COPY --from=builder /app/build/libs/*.jar /app/app.jar",
        "cmd": '["java", "-jar", "/app/app.jar"]',
        "health_path": "/actuator/health",
    },
    # Ruby
    "rails": {
        "port": 3000, "base_image": "ruby:3.3-slim",
        "dep_copy": "COPY Gemfile Gemfile.lock* ./",
        "install": "RUN bundle install --without development test",
        "build": "RUN bundle exec rake assets:precompile 2>/dev/null || true",
        "cmd": '["bundle", "exec", "rails", "server", "-b", "0.0.0.0"]',
        "health_path": "/",
    },
    "ruby": {
        "port": 3000, "base_image": "ruby:3.3-slim",
        "dep_copy": "COPY Gemfile Gemfile.lock* ./",
        "install": "RUN bundle install --without development test",
        "cmd": '["ruby", "{entry}"]',
        "entry_detect": ["app.rb", "server.rb", "main.rb", "config.ru"],
        "health_path": "/",
    },
    # PHP
    "php": {
        "port": 80, "base_image": "php:8.3-apache",
        "dep_copy": "COPY composer.json composer.lock* ./",
        "install": (
            "RUN curl -sS https://getcomposer.org/installer | php -- "
            "--install-dir=/usr/local/bin --filename=composer "
            "&& composer install --no-dev --optimize-autoloader 2>/dev/null || true"
        ),
        "cmd": '["apache2-foreground"]',
        "health_path": "/",
    },
    # .NET
    "dotnet": {
        "port": 8080, "base_image": "mcr.microsoft.com/dotnet/sdk:8.0",
        "dep_copy": "COPY *.csproj ./",
        "install": "RUN dotnet restore",
        "build": "RUN dotnet publish -c Release -o /app/publish",
        "runtime_image": "mcr.microsoft.com/dotnet/aspnet:8.0",
        "runtime_copy": "COPY --from=builder /app/publish /app",
        "cmd": '["dotnet", "app.dll"]',
        "health_path": "/health",
    },
    # Static HTML
    "static": {
        "port": 80, "base_image": "nginx:alpine",
        "dep_copy": "",
        "install": "",
        "cmd": '["nginx", "-g", "daemon off;"]',
        "health_path": "/",
    },
}


# ------------------------------------------------------------------
# Detection
# ------------------------------------------------------------------

def _detect_java_version(path: Path) -> int:
    """
    Read the Java version required by the project.
    Checks build.gradle, build.gradle.kts, and .java-version.
    Returns 17 as a safe default.
    """
    for fname in ["build.gradle", "build.gradle.kts", "pom.xml"]:
        f = path / fname
        if not f.exists():
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="ignore")
            # toolchain { languageVersion = JavaLanguageVersion.of(17) }
            m = re.search(r"JavaLanguageVersion\.of\((\d+)\)", txt)
            if m:
                return int(m.group(1))
            # sourceCompatibility = '17'  or  = JavaVersion.VERSION_17
            m = re.search(r"sourceCompatibility\s*=\s*['\"]?(\d+)['\"]?", txt)
            if m:
                return int(m.group(1))
            m = re.search(r"VERSION_(\d+)", txt)
            if m:
                return int(m.group(1))
            # Maven: <java.version>17</java.version>
            m = re.search(r"<java\.version>(\d+)</java\.version>", txt)
            if m:
                return int(m.group(1))
        except Exception:
            pass
    # .java-version file (jenv / sdkman)
    jv = path / ".java-version"
    if jv.exists():
        try:
            ver = jv.read_text(encoding="utf-8").strip().split(".")[0]
            return int(ver)
        except Exception:
            pass
    return 17  # safe default


def detect_framework(path: Path) -> tuple[str, dict]:
    """Inspect project directory and return (framework_name, profile)."""
    try:
        files = {f.name.lower() for f in path.iterdir() if f.is_file()}
    except Exception:
        return "python", PROFILES["python"]

    # .NET
    if any(f.endswith(".csproj") or f.endswith(".fsproj") for f in files):
        return "dotnet", PROFILES["dotnet"]
    # Java
    if "pom.xml" in files:
        return "java-maven", PROFILES["java-maven"]
    if "build.gradle" in files or "build.gradle.kts" in files:
        return "java-gradle", PROFILES["java-gradle"]
    # Go
    if "go.mod" in files:
        return "go", PROFILES["go"]
    # Rust
    if "cargo.toml" in files:
        return "rust", PROFILES["rust"]
    # Ruby
    if "gemfile" in files:
        try:
            txt = (path / "Gemfile").read_text(encoding="utf-8", errors="ignore").lower()
            fw = "rails" if "rails" in txt else "ruby"
        except Exception:
            fw = "ruby"
        return fw, PROFILES[fw]
    # PHP
    if "composer.json" in files or any(f.endswith(".php") for f in files):
        return "php", PROFILES["php"]
    # Node.js
    if "package.json" in files:
        try:
            pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
            deps = dict(**pkg.get("dependencies", {}), **pkg.get("devDependencies", {}))
            if "next" in deps:
                return "nextjs", PROFILES["nextjs"]
            if "react" in deps or "react-dom" in deps:
                return "react", PROFILES["react"]
        except Exception:
            pass
        return "nodejs", PROFILES["nodejs"]
    # Python
    reqs = ""
    if "requirements.txt" in files:
        try:
            reqs += (path / "requirements.txt").read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            pass
    if "pyproject.toml" in files:
        try:
            reqs += (path / "pyproject.toml").read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            pass
    if reqs or "setup.py" in files:
        for kw, fw in [("fastapi", "fastapi"), ("uvicorn", "fastapi"),
                       ("django", "django"), ("streamlit", "streamlit"),
                       ("flask", "flask")]:
            if kw in reqs:
                return fw, PROFILES[fw]
        return "python", PROFILES["python"]
    if any(f.endswith(".py") for f in files):
        return "python", PROFILES["python"]
    # Static
    if "index.html" in files or any(f.endswith(".html") for f in files):
        return "static", PROFILES["static"]
    # Default
    return "python", PROFILES["python"]


def _find_entry(path: Path, profile: dict) -> str:
    """Return the actual entry-point filename that exists in path."""
    for candidate in profile.get("entry_detect", []):
        if (path / candidate).exists():
            return candidate
    py_files = sorted(path.glob("*.py"))
    return py_files[0].name if py_files else "main.py"


def _resolve_cmd(profile: dict, entry: str) -> str:
    """Fill {entry} and {entry_module} placeholders in the CMD string."""
    module = entry.replace(".py", "").replace("/", ".").replace("\\", ".")
    return profile["cmd"].replace("{entry}", entry).replace("{entry_module}", module)


# ------------------------------------------------------------------
# Dockerfile generation  (100% ASCII content)
# ------------------------------------------------------------------

def generate_dockerfile(path: Path, framework: str, profile: dict) -> Path:
    """Write an optimised Dockerfile (ASCII only) and return its path."""
    port    = profile["port"]
    health  = profile.get("health_path", "/")
    entry   = _find_entry(path, profile)
    cmd     = _resolve_cmd(profile, entry)
    dep     = profile.get("dep_copy", "")
    install = profile.get("install", "")
    build   = profile.get("build", "")

    # For Java projects: detect the required JDK version and pick matching images
    if framework in ("java-gradle", "java-maven"):
        jv = _detect_java_version(path)
        profile = dict(profile)   # don't mutate the global
        if framework == "java-gradle":
            profile["base_image"]    = "gradle:8-jdk{}".format(jv)
            profile["runtime_image"] = "eclipse-temurin:{}-jre-alpine".format(jv)
            profile["build"] = (
                "RUN ./gradlew bootJar --no-daemon -q "
                "-Porg.gradle.java.installations.auto-detect=false "
                "-Porg.gradle.java.installations.auto-download=false "
                "2>/dev/null || ./gradlew jar --no-daemon -q "
                "-Porg.gradle.java.installations.auto-detect=false "
                "-Porg.gradle.java.installations.auto-download=false"
            )
            build = profile["build"]
        elif framework == "java-maven":
            profile["base_image"]    = "maven:3.9-eclipse-temurin-{}".format(jv)
            profile["runtime_image"] = "eclipse-temurin:{}-jre-alpine".format(jv)

    base_image = profile["base_image"]

    header = (
    ).format(framework, entry, port)

    if "runtime_image" in profile:
        body = (
            header + "\n"
            "# -- Stage 1: build ------------------------------------------------\n"
            "FROM {} AS builder\n"
            "WORKDIR /app\n\n"
            "{}\n"
            "{}\n\n"
            "COPY . .\n"
            "{}\n\n"
            "# -- Stage 2: runtime ----------------------------------------------\n"
            "FROM {}\n"
            "WORKDIR /app\n"
            "{}\n\n"
            "EXPOSE {}\n"
            "CMD {}\n"
        ).format(
            base_image,
            dep, install, build,
            profile["runtime_image"],
            profile.get("runtime_copy", "COPY --from=builder /app /app"),
            port, cmd,
        )
    else:
        # Non-root user only for slim/alpine images
        nonroot = ""
        if any(x in base_image for x in ("alpine", "slim", "debian", "ubuntu")):
            nonroot = (
                "\n# Security: run as non-root\n"
                "RUN addgroup --system appgroup "
                "&& adduser --system --ingroup appgroup appuser 2>/dev/null || true\n"
                "USER appuser\n"
            )

        healthcheck = (
            "\nHEALTHCHECK --interval=30s --timeout=5s "
            "--start-period=15s --retries=3 \\\n"
            "    CMD wget -qO- http://localhost:{}{} 2>/dev/null || exit 0\n"
        ).format(port, health)

        body = (
            header + "\n"
            "FROM {}\n"
            "WORKDIR /app\n\n"
            "# Install dependencies first (better layer caching)\n"
            "{}\n"
            "{}\n\n"
            "# Copy full project source\n"
            "COPY . .\n"
            "{}\n"
            "{}"
            "{}\n"
            "EXPOSE {}\n"
            "CMD {}\n"
        ).format(
            base_image,
            dep, install, build,
            nonroot, healthcheck,
            port, cmd,
        )

    df = path / "Dockerfile"
    # encoding="utf-8" is REQUIRED on Windows to avoid cp1252 errors
    df.write_text(body, encoding="utf-8")
    return df


# ------------------------------------------------------------------
# Docker helpers
# ------------------------------------------------------------------

def _safe_name(s: str) -> str:
    return re.sub(r"[^a-z0-9_-]", "-", s.lower()).strip("-") or "myapp"

def _docker_ok() -> bool:
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0

def _kubectl_ok() -> bool:
    return subprocess.run(["kubectl", "version", "--client"], capture_output=True).returncode == 0

def _compose_exe() -> list:
    r = subprocess.run(["docker", "compose", "version"], capture_output=True)
    return ["docker", "compose"] if r.returncode == 0 else ["docker-compose"]

def _dotenv(path: Path) -> dict:
    env = {}
    for name in [".env", ".env.local", ".env.production"]:
        p = path / name
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, _, v = line.partition("=")
                        env.setdefault(k.strip(), v.strip())
            except Exception:
                pass
    return env

def _run(cmd: list, cwd=None, extra_env=None) -> bool:
    _info(" ".join(str(c) for c in cmd))
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(cmd, cwd=cwd, env=env)
    return r.returncode == 0

def build_image(path: Path, tag: str) -> bool:
    return _run(["docker", "build", "-t", tag, "."],
                cwd=path, extra_env={"DOCKER_BUILDKIT": "1"})

def push_image(local: str, registry: str) -> tuple:
    remote = "{}/{}:latest".format(registry, local.split(":")[0])
    if not _run(["docker", "tag", local, remote]):
        return False, remote
    ok = _run(["docker", "push", remote])
    return ok, remote


# ------------------------------------------------------------------
# docker-compose generation
# ------------------------------------------------------------------

def generate_compose(path: Path, image: str, svc: str,
                     port: int, env: dict) -> Path:
    env_block = ""
    if env:
        lines = "\n".join("      - {}={}".format(k, v) for k, v in env.items())
        env_block = "    environment:\n{}\n".format(lines)

    body = (
        "# Auto-generated by ai:deploy\n"
        "version: \"3.9\"\n\n"
        "services:\n"
        "  {}:\n"
        "    image: {}\n"
        "    container_name: {}-container\n"
        "    restart: unless-stopped\n"
        "    ports:\n"
        "      - \"{}:{}\"\n"
        "{}"
        "    healthcheck:\n"
        "      test: [\"CMD-SHELL\","
        " \"wget -qO- http://localhost:{}/ 2>/dev/null || exit 0\"]\n"
        "      interval: 30s\n"
        "      timeout: 10s\n"
        "      retries: 3\n"
        "      start_period: 15s\n"
        "    logging:\n"
        "      driver: json-file\n"
        "      options:\n"
        "        max-size: \"10m\"\n"
        "        max-file: \"3\"\n\n"
        "networks:\n"
        "  default:\n"
        "    name: {}-network\n"
    ).format(svc, image, svc, port, port, env_block, port, svc)

    f = path / "docker-compose.yml"
    f.write_text(body, encoding="utf-8")
    return f


def compose_up(path: Path) -> bool:
    return _run(_compose_exe() + ["up", "-d", "--remove-orphans"], cwd=path)

def compose_down(path: Path) -> bool:
    return _run(_compose_exe() + ["down", "--volumes", "--remove-orphans"], cwd=path)


# ------------------------------------------------------------------
# Kubernetes manifest generation
# ------------------------------------------------------------------

def generate_k8s_manifests(path: Path, image: str, name: str,
                            port: int, env: dict, replicas: int = 2) -> Path:
    env_block = ""
    if env:
        lines = "\n".join(
            "          - name: {}\n            value: \"{}\"".format(k, v)
            for k, v in env.items()
        )
        env_block = "        env:\n{}\n".format(lines)

    body = (
        "# Auto-generated by ai:deploy  |  app: {name}\n"
        "---\n"
        "apiVersion: v1\n"
        "kind: Namespace\n"
        "metadata:\n"
        "  name: {name}\n"
        "  labels:\n"
        "    managed-by: ai-deploy\n"
        "---\n"
        "apiVersion: apps/v1\n"
        "kind: Deployment\n"
        "metadata:\n"
        "  name: {name}\n"
        "  namespace: {name}\n"
        "  labels:\n"
        "    app: {name}\n"
        "    managed-by: ai-deploy\n"
        "spec:\n"
        "  replicas: {replicas}\n"
        "  selector:\n"
        "    matchLabels:\n"
        "      app: {name}\n"
        "  template:\n"
        "    metadata:\n"
        "      labels:\n"
        "        app: {name}\n"
        "    spec:\n"
        "      containers:\n"
        "        - name: {name}\n"
        "          image: {image}\n"
        "          imagePullPolicy: Always\n"
        "          ports:\n"
        "            - containerPort: {port}\n"
        "{env_block}"
        "          resources:\n"
        "            requests:\n"
        "              cpu: \"100m\"\n"
        "              memory: \"128Mi\"\n"
        "            limits:\n"
        "              cpu: \"500m\"\n"
        "              memory: \"512Mi\"\n"
        "          livenessProbe:\n"
        "            httpGet:\n"
        "              path: /\n"
        "              port: {port}\n"
        "            initialDelaySeconds: 15\n"
        "            periodSeconds: 20\n"
        "          readinessProbe:\n"
        "            httpGet:\n"
        "              path: /\n"
        "              port: {port}\n"
        "            initialDelaySeconds: 5\n"
        "            periodSeconds: 10\n"
        "      securityContext:\n"
        "        runAsNonRoot: true\n"
        "        runAsUser: 1000\n"
        "---\n"
        "apiVersion: v1\n"
        "kind: Service\n"
        "metadata:\n"
        "  name: {name}-service\n"
        "  namespace: {name}\n"
        "  labels:\n"
        "    app: {name}\n"
        "    managed-by: ai-deploy\n"
        "spec:\n"
        "  selector:\n"
        "    app: {name}\n"
        "  ports:\n"
        "    - protocol: TCP\n"
        "      port: 80\n"
        "      targetPort: {port}\n"
        "  type: LoadBalancer\n"
        "---\n"
        "apiVersion: autoscaling/v2\n"
        "kind: HorizontalPodAutoscaler\n"
        "metadata:\n"
        "  name: {name}-hpa\n"
        "  namespace: {name}\n"
        "spec:\n"
        "  scaleTargetRef:\n"
        "    apiVersion: apps/v1\n"
        "    kind: Deployment\n"
        "    name: {name}\n"
        "  minReplicas: {replicas}\n"
        "  maxReplicas: 10\n"
        "  metrics:\n"
        "    - type: Resource\n"
        "      resource:\n"
        "        name: cpu\n"
        "        target:\n"
        "          type: Utilization\n"
        "          averageUtilization: 70\n"
    ).format(name=name, image=image, port=port,
             replicas=replicas, env_block=env_block)

    d = path / "k8s"
    d.mkdir(exist_ok=True)
    f = d / "deployment.yaml"
    f.write_text(body, encoding="utf-8")
    return f


def k8s_apply(f: Path) -> bool:
    return _run(["kubectl", "apply", "-f", str(f)])

def k8s_wait(name: str) -> bool:
    return _run([
        "kubectl", "rollout", "status",
        "deployment/{}".format(name),
        "-n={}".format(name),
        "--timeout=120s",
    ])

def k8s_delete(name: str) -> bool:
    return _run(["kubectl", "delete", "namespace", name, "--ignore-not-found=true"])

def k8s_url(name: str) -> str:
    for field in (".status.loadBalancer.ingress[0].ip",
                  ".status.loadBalancer.ingress[0].hostname"):
        r = subprocess.run(
            ["kubectl", "get", "svc", "{}-service".format(name),
             "-n={}".format(name),
             "-o=jsonpath={{{}}}".format(field)],
            capture_output=True, text=True,
        )
        if r.stdout.strip():
            return r.stdout.strip()
    return "<pending -- run: kubectl get svc -n {}>".format(name)


# ------------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------------

def run_deploy_docker(
    project_path=".",
    image_name=None,
    registry=None,
    overwrite_dockerfile=True,
) -> int:
    """One-click Docker deployment. Returns 0 on success, 1 on failure."""
    path = Path(project_path).resolve()
    if not image_name:
        image_name = _safe_name(path.name)

    total = 6 + (1 if registry else 0)
    _banner("ai:deploy docker  --  One-Click Container Deployment")

    if not path.is_dir():
        _fail("Directory not found: {}".format(path)); return 1
    if not _docker_ok():
        _fail("Docker is not running -- start Docker Desktop first"); return 1

    _step(1, total, "Detecting language / framework ...")
    fw, profile = detect_framework(path)
    entry = _find_entry(path, profile)
    _ok("Language: {}   Port: {}   Entry: {}".format(
        _c("bold", fw), profile["port"], entry))

    _step(2, total, "Generating Dockerfile ...")
    df = path / "Dockerfile"
    if df.exists() and not overwrite_dockerfile:
        _warn("Keeping existing Dockerfile")
    else:
        generate_dockerfile(path, fw, profile)
        _ok("Wrote {}".format(df))

    local_tag = "{}:latest".format(image_name)
    _step(3, total, "Building image  {} ...".format(_c("bold", local_tag)))
    if not build_image(path, local_tag):
        _fail("docker build failed -- see output above"); return 1
    _ok("Image ready: {}".format(local_tag))

    img4compose = local_tag
    if registry:
        _step(4, total, "Pushing to {} ...".format(_c("bold", registry)))
        ok, remote = push_image(local_tag, registry)
        if ok:
            img4compose = remote
            _ok("Pushed: {}".format(remote))
        else:
            _warn("Push failed -- using local image")

    n = 5 if registry else 4
    _step(n, total, "Writing docker-compose.yml ...")
    cfile = generate_compose(path, img4compose, image_name,
                             profile["port"], _dotenv(path))
    _ok("Wrote {}".format(cfile))

    n = 6 if registry else 5
    _step(n, total, "Starting containers ...")
    if not compose_up(path):
        _fail("docker compose up failed"); return 1
    _ok("Containers running!")

    n = 7 if registry else 6
    _step(n, total, "Done!")
    url = "http://localhost:{}".format(profile["port"])
    print("\n  +--------------------------------------------------------------+")
    print("  |                                                              |")
    print("  |   {}                          |".format(
        _c("green", _c("bold", "DOCKER DEPLOYMENT SUCCESSFUL"))))
    print("  |                                                              |")
    print("  |   Language  :  {:<46}|".format(fw))
    print("  |   Image     :  {:<46}|".format(local_tag))
    print("  |   Access    :  {:<46}|".format(url))
    print("  |                                                              |")
    print("  |   docker compose logs -f                                     |")
    print("  |   docker compose ps                                          |")
    print("  |   ai:destroy  <-- one-click teardown                         |")
    print("  |                                                              |")
    print("  +--------------------------------------------------------------+\n")
    return 0


def run_deploy_k8s(
    project_path=".",
    image_name=None,
    registry=None,
    replicas=2,
    overwrite_dockerfile=True,
) -> int:
    """One-click Kubernetes deployment. Returns 0 on success, 1 on failure."""
    path = Path(project_path).resolve()
    if not image_name:
        image_name = _safe_name(path.name)

    _banner("ai:deploy kubernetes  --  One-Click K8s Deployment")

    if not path.is_dir():
        _fail("Directory not found: {}".format(path)); return 1
    if not _docker_ok():
        _fail("Docker is not running"); return 1
    if not _kubectl_ok():
        _fail("kubectl not found -- install kubectl and configure a cluster"); return 1

    _step(1, 7, "Detecting language / framework ...")
    fw, profile = detect_framework(path)
    entry = _find_entry(path, profile)
    _ok("Language: {}   Port: {}   Entry: {}".format(
        _c("bold", fw), profile["port"], entry))

    _step(2, 7, "Generating Dockerfile ...")
    df = path / "Dockerfile"
    if df.exists() and not overwrite_dockerfile:
        _warn("Keeping existing Dockerfile")
    else:
        generate_dockerfile(path, fw, profile)
        _ok("Wrote {}".format(df))

    local_tag = "{}:latest".format(image_name)
    _step(3, 7, "Building image  {} ...".format(_c("bold", local_tag)))
    if not build_image(path, local_tag):
        _fail("docker build failed"); return 1
    _ok("Image ready: {}".format(local_tag))

    img4k8s = local_tag
    if not registry:
        _warn("No --registry given. K8s nodes may not pull a local-only image.")
        _warn("Fine for minikube/kind; for cloud clusters add --registry.")
    else:
        _step(4, 7, "Pushing to {} ...".format(_c("bold", registry)))
        ok, remote = push_image(local_tag, registry)
        if ok:
            img4k8s = remote
            _ok("Pushed: {}".format(remote))
        else:
            _warn("Push failed -- continuing with local image")

    _step(5, 7, "Generating k8s/deployment.yaml ...")
    mf = generate_k8s_manifests(
        path, img4k8s, image_name, profile["port"], _dotenv(path), replicas)
    _ok("Wrote {}".format(mf))

    _step(6, 7, "Applying manifests ...")
    if not k8s_apply(mf):
        _fail("kubectl apply failed"); return 1
    _ok("Manifests applied")

    _step(7, 7, "Waiting for rollout ...")
    k8s_wait(image_name)
    svc = k8s_url(image_name)
    _ok("Rollout complete")

    print("\n  +--------------------------------------------------------------+")
    print("  |                                                              |")
    print("  |   {}                     |".format(
        _c("green", _c("bold", "KUBERNETES DEPLOYMENT SUCCESSFUL"))))
    print("  |                                                              |")
    print("  |   Language   : {:<46}|".format(fw))
    print("  |   Image      : {:<46}|".format(img4k8s))
    print("  |   Namespace  : {:<46}|".format(image_name))
    print("  |   Replicas   : {:<46}|".format(str(replicas)))
    print("  |   Service    : {:<46}|".format(svc))
    print("  |                                                              |")
    print("  |   kubectl get pods -n {}".format(image_name))
    print("  |   ai:destroy --target kubernetes  <-- teardown               |")
    print("  |                                                              |")
    print("  +--------------------------------------------------------------+\n")
    return 0


def run_destroy(
    project_path=".",
    image_name=None,
    target="docker",
) -> int:
    """Tear down Docker and/or Kubernetes resources. Returns 0."""
    path = Path(project_path).resolve()
    if not image_name:
        image_name = _safe_name(path.name)

    _banner("ai:destroy  --  One-Click Teardown")

    if target in ("docker", "all"):
        _step(1, 3, "Stopping Docker Compose services ...")
        if (path / "docker-compose.yml").exists():
            ok = compose_down(path)
            _ok("Compose stopped") if ok else _warn("compose down had errors (continuing)")
        else:
            _warn("No docker-compose.yml found")

        _step(2, 3, "Removing image  {}:latest ...".format(image_name))
        r = subprocess.run(
            ["docker", "rmi", "-f", "{}:latest".format(image_name)],
            capture_output=True,
        )
        _ok("Image removed") if r.returncode == 0 else _warn("Image not found or already removed")

    if target in ("kubernetes", "all"):
        n = 3 if target == "all" else 1
        tot = 3 if target == "all" else 2
        _step(n, tot, "Deleting K8s namespace  {} ...".format(image_name))
        ok = k8s_delete(image_name)
        _ok("Namespace '{}' deleted".format(image_name)) if ok \
            else _warn("kubectl delete had errors (continuing)")

        if target != "all":
            _step(2, 2, "Removing image  {}:latest ...".format(image_name))
            r = subprocess.run(
                ["docker", "rmi", "-f", "{}:latest".format(image_name)],
                capture_output=True,
            )
            _ok("Image removed") if r.returncode == 0 else _warn("Image already gone")

    print("\n  [DONE] Environment is clean.\n")
    return 0
